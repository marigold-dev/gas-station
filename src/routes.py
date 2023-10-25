from src import database
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import src.crud as crud
import src.schemas as schemas
import uuid

from sqlalchemy.orm import Session
from . import tezos
from pytezos.rpc.errors import MichelsonError
from .utils import ContractNotFound, CreditNotFound, EntrypointNotFound, UserNotFound


router = APIRouter()

#! API Routes


# Healthcheck
@router.get("/")
async def root():
    return {"message": "Hello World"}


# POST endpoints
@router.post("/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreation, db: Session = Depends(database.get_db)
):
    user = crud.create_user(db, user)
    crud.create_credits(db, schemas.CreditCreation(owner_id = user.id))
    return user


@router.post("/contracts", response_model=schemas.Contract)
async def create_contract(
    contract: schemas.ContractCreation, db: Session = Depends(database.get_db)
):
    return crud.create_contract(db, contract)


# PUT endpoints
@router.put("/entrypoints", response_model=list[schemas.Entrypoint])
async def update_entrypoints(
    entrypoints: list[schemas.EntrypointUpdate], db: Session = Depends(database.get_db)
):
    return crud.update_entrypoints(db, entrypoints)


@router.put("/deposit", response_model=schemas.Credit)
async def update_credits(
    credits: schemas.CreditUpdate, db: Session = Depends(database.get_db)
):
    try:
        payer_address = crud.get_user(db, credits.owner_id).address
        op_hash = credits.operation_hash
        amount = credits.amount
        is_confirmed = await tezos.confirm_deposit(op_hash,
                                                   payer_address,
                                                   amount)
        if not is_confirmed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not find confirmation for {amount} with {op_hash}"
            )
        return crud.update_credits(db, credits)
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


@router.put("/withdraw")
async def withdraw_credits(
    withdraw: schemas.CreditWithdraw, db: Session = Depends(database.get_db)
):
    try:
        credits = crud.get_credits(db, withdraw.id)
    except CreditNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit not found.",
        )
    if credits.amount < withdraw.amount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Not enough funds to withdraw."
        )

    owner_address = credits.owner.address
    user = crud.get_user_by_address(db, owner_address)
    public_key = tezos.get_public_key(owner_address)
    is_valid = tezos.check_signature(withdraw.to_micheline_pair(),
                                     withdraw.micheline_signature,
                                     public_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid signature."
        )
    result = await tezos.withdraw(tezos.tezos_manager,
                                  owner_address,
                                  withdraw.amount)
    if result["result"] == "ok":
        credit_update = schemas.CreditUpdate(id=withdraw.id,
                                             amount=-withdraw.amount,
                                             # FIXME I guess
                                             owner_id=str(user.id),
                                             operation_hash="")
        crud.update_credits(db, credit_update)
    return result


# Users and credits getters
@router.get("/users/{user_address}", response_model=schemas.User)
async def get_user(user_address: str, db: Session = Depends(database.get_db)):
    try:
        return crud.get_user_by_address(db, user_address)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found.",
        )


@router.get("/credits/{user_id}", response_model=list[schemas.Credit])
async def credits_for_user(
    user_id: str, db: Session = Depends(database.get_db)
):
    try:
        return crud.get_user(db, user_id).credits
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found.",
        )


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
async def get_credit(credit_id: str, db: Session = Depends(database.get_db)):
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
    # TODO: check that amount=0?
    for operation in call_data.operations:
        contract_address = str(operation["destination"])

        # Transfers to implicit accounts are always refused
        if not contract_address.startswith("KT"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Target {contract_address} is not allowed",
            )
        try:
            contract = crud.get_contract(db, contract_address)
        except ContractNotFound:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Target {contract_address} is not allowed",
            )

        entrypoint_name = operation["parameters"]["entrypoint"]
        print(contract_address, entrypoint_name)
        try:
            entrypoint = crud.get_entrypoint(db,
                                             str(contract.address),
                                             entrypoint_name)
        except EntrypointNotFound:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Entrypoint {entrypoint_name} is not allowed",
            )

    try:
        # Simulate the operation alone without sending it
        # TODO: log the result
        op = tezos.simulate_transaction(call_data.operations)
        op_estimated_fees = [(int(x["fee"]), x["destination"])
                             for x in op.contents]
        estimated_fees = tezos.group_fees(op_estimated_fees)
        if not tezos.check_credits(db, estimated_fees):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Not enough funds."
            )
        result = await tezos.tezos_manager.queue_operation(call_data.sender,
                                                           op)
    except MichelsonError as e:
        print("Received failing operation, discarding")
        print(e)
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation is invalid",
        )
    except Exception:
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown exception raised.",
        )
    return result
