from src import database
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import src.crud as crud
import src.schemas as schemas

from sqlalchemy.orm import Session
from .tezos import tezos_manager, ptz, confirm_amount
from pytezos.rpc.errors import MichelsonError
from .utils import ContractNotFound, CreditNotFound, EntrypointNotFound, UserNotFound


router = APIRouter()

#! API Routes


# Healthcheck
@router.get("/")
async def root():
    return {"message": "Hello World"}


# Users
@router.get("/users/{user_address}", response_model=schemas.User)
async def get_user(user_address: str, db: Session = Depends(database.get_db)):
    try:
        return crud.get_user(db, user_address)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found.",
        )


@router.post("/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreation, db: Session = Depends(database.get_db)
):
    user = crud.create_user(db, user)
    crud.create_credits(db, schemas.CreditCreation(owner_id = user.id))
    return user


# Contracts
@router.get("/contracts/user/{user_address}", response_model=list[schemas.Contract])
async def get_user_contracts(user_address: str, db: Session = Depends(database.get_db)):
    try:
        return crud.get_contracts_by_user(db, user_address)
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found."
        )


@router.get("/contracts/credit/{credit_id}",
            response_model=list[schemas.Contract])
async def get_user_contracts(credit_id: str, db: Session = Depends(database.get_db)):
    try:
        return crud.get_contracts_by_credit(db, credit_id)
    except CreditNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Credit not found."
        )


@router.get("/contracts/{address}", response_model=schemas.Contract)
async def get_contract(address: str, db: Session = Depends(database.get_db)):
    contract = crud.get_contract(db, address)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract not found."
        )
    return contract


@router.post("/contracts", response_model=schemas.Contract)
async def create_contract(
    contract: schemas.ContractCreation, db: Session = Depends(database.get_db)
):
    return crud.create_contract(db, contract)


# Entrypoints
@router.get("/entrypoints/{contract_address}", response_model=list[schemas.Entrypoint])
async def get_entrypoints(
    contract_address: str, db: Session = Depends(database.get_db)
):
    try:
        return crud.get_entrypoints(db, contract_address)
    except ContractNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract not found."
        )

@router.get("/entrypoints/{contract_address}/{name}", response_model=schemas.Entrypoint)
async def get_entrypoint(
    contract_address: str, name: str, db: Session = Depends(database.get_db)
):
    try:
        return crud.get_entrypoint(db, contract_address, name)
    except EntrypointNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entrypoint not found."
        )


@router.put("/entrypoints", response_model=list[schemas.Entrypoint])
async def update_entrypoints(
    entrypoints: list[schemas.EntrypointUpdate], db: Session = Depends(database.get_db)
):
    return crud.update_entrypoints(db, entrypoints)


# Operations
@router.post("/operation")
async def post_operation(
    call_data: schemas.CallData, db: Session = Depends(database.get_db)
):
    if len(call_data.operations) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Empty operations list",
        )
    operation_ids = []
    # TODO: check that amount=0?
    for operation in call_data.operations:
        print(operation)
        contract_address = str(operation["destination"])

        # Transfers to implicit accounts are always refused
        if not contract_address.startswith("KT"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Target {contract_address} is not allowed",
            )
        contract = crud.get_contract(db, contract_address)
        if contract is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Target {contract_address} is not allowed",
            )

        entrypoint_name = operation["parameters"]["entrypoint"]
        print(contract_address, entrypoint_name)
        entrypoint = crud.get_entrypoint(db, str(contract.address), entrypoint_name)

        if entrypoint is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Entrypoint {entrypoint_name} is not allowed",
            )
        # Create operation with contract/entrypoint
        db_operation = crud.create_operation(
            db,
            schemas.CreateOperation(
                contract_id=str(contract.id), entrypoint_id=str(entrypoint.id)
            ),
        )
        operation_ids.append(db_operation.id)

    # FIXME move to tezos module
    op = ptz.bulk(
        *[
            ptz.transaction(
                source=ptz.key.public_key_hash(),
                parameters=operation["parameters"],
                destination=operation["destination"],
                amount=0,
            )
            for operation in call_data.operations
        ]  # type: ignore
    )
    # TODO: log the result

    try:
        # Simulate the operation alone without sending it
        op.autofill()
        result = await tezos_manager.queue_operation(call_data.sender, op)
    except MichelsonError as e:
        print("Received failing operation, discarding")
        print(e)
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation is invalid",
        )

    for op_id in operation_ids:
        crud.update_operation(
            db,
            op_id,
            result["transaction_hash"],
            status="ok" if result["result"] == "ok" else "failed",
        )

    if result["result"] == "failing":
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation is invalid",
        )
    return result


# Credits
# TODO handle negative amount (withdraw)
@router.put("/credits", response_model=schemas.Credit)
async def update_credits(
    credits: schemas.CreditUpdate, db: Session = Depends(database.get_db)
):
    try:
        payer_address = crud.get_user(db, credits.owner_id)
        op_hash = credits.operation_hash
        amount = credits.amount
        is_confirmed = confirm_amount(op_hash, payer_address, amount)
        if not is_confirmed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not find confirmation for {amount} with {op_hash}"
            )
        return crud.update_credits(db, amount, credits.contract_address)
    except ContractNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contrat not found.",
        )
    except CreditNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit not found.",
        )
