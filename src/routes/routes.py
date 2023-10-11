from src import database
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import src.crud as crud
import src.schemas as schemas

from sqlalchemy.orm import Session


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

