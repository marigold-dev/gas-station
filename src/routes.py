from src import database
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import src.crud as crud
import src.schemas as schemas

from sqlalchemy.orm import Session
from .pytezos import ptz, pytezos
from .tezos_manager import tezos_manager
from pytezos.rpc.errors import MichelsonError



router = APIRouter()

#! API Routes

# Healthcheck
@router.get("/")
async def root():
    return {"message": "Hello World"}


# Users
@router.get("/users/{user_address}", response_model=schemas.User)
async def get_user(user_address: str, db: Session = Depends(database.get_db)):
    return crud.get_user(db, user_address)


@router.post("/users", response_model=schemas.User)
async def create_user(user: schemas.UserCreation, db: Session = Depends(database.get_db)):
    return crud.create_user(db, user)


@router.put("/users/credits", response_model=schemas.User)
async def update_credits(credits: schemas.UserUpdateCredit, db: Session = Depends(database.get_db)):
    return crud.update_credits(db, credits)


# Contracts
@router.get("/contracts/user/{user_address}", response_model=list[schemas.Contract])
async def get_user_contracts(user_address: str, db: Session = Depends(database.get_db)):
    contracts = crud.get_contracts_by_user(db, user_address)
    if not contracts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found."
        )
    return contracts


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
    entrypoints = crud.get_entrypoints(db, contract_address)
    return entrypoints


@router.get("/entrypoints/{contract_address}/{name}", response_model=schemas.Entrypoint)
async def get_entrypoint(
    contract_address: str, name: str, db: Session = Depends(database.get_db)
):
    entrypoint = crud.get_entrypoint(db, contract_address, name)
    if not entrypoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entrypoint not found."
        )
    return entrypoint

@router.put("/entrypoints", response_model=list[schemas.Entrypoint])
async def update_entrypoints(entrypoints: list[schemas.EntrypointUpdate], db: Session = Depends(database.get_db)):
    return crud.update_entrypoints(db, entrypoints)


# Operations
@router.post("/operation")
async def post_operation(call_data: schemas.CallData, db: Session = Depends(database.get_db)):
    if len(call_data.operations) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Empty operations list"
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
                    detail=f"Target {contract_address} is not allowed"
                )
        contract = crud.get_contract(db, contract_address)
        if contract is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Target {contract_address} is not allowed"
            )

        entrypoint_name = operation["parameters"]["entrypoint"]
        print(contract_address, entrypoint_name)
        entrypoint = crud.get_entrypoint(db, str(contract.address), entrypoint_name)

        if entrypoint is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Entrypoint {entrypoint_name} is not allowed"
            )
        # Create operation with contract/entrypoint
        db_operation = crud.create_operation(db, schemas.CreateOperation(contract_id=str(contract.id), entrypoint_id=str(entrypoint.id)))
        operation_ids.append(db_operation.id)

    op = ptz.bulk(*[
        ptz.transaction(
            source=ptz.key.public_key_hash(),
            parameters=operation["parameters"],
            destination=operation["destination"],
            amount=0
        )
        for operation in call_data.operations
    ]) # type: ignore
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
            detail=f"Operation is invalid"
            )
    print(result["transaction_hash"], result['result'])
    for op_id in operation_ids:
        crud.update_operation(db, op_id, result["transaction_hash"], status="ok" if result['result'] == 'ok' else 'failed')
    # if result == 'ok':
        # crud.create_operation(db, schemas.CreateOperation(contract_address=operation["destination"], entrypoint_name=operation["parameters"]["entrypoint"],transaction_hash=op['transaction_hash']))
    if result == "failing":
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation is invalid"
        )
    return result