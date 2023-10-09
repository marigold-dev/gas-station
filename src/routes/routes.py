from src import database
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List
from src.schemas import UserBase
import src.crud as crud
import src.schemas as schemas

from sqlalchemy.orm import Session


router = APIRouter()

#! Entities for creation routes
class User(BaseModel):
    user_name: str
    user_address: str | None

class Entrypoint(BaseModel):
    entrypoint_name: str
    is_enabled: bool


class Contract(BaseModel):
  contract_name: str
  contract_address: str
  entrypoints: List[Entrypoint]
  owner_address: str


#! API Routes

# Healthcheck
@router.get("/")
async def root():
    return {"message": "Hello World"}

# Users

@router.get("/users/{user_address}", response_model=schemas.User)
async def get_user(user_address: str, db: Session = Depends(database.get_db)):
    db_user = crud.get_user(db, user_address)
    print(db_user)
    return db_user

@router.post('/users', response_model=schemas.User)
async def create_user(user: User, db: Session = Depends(database.get_db)):
    return crud.create_user(db, user)


# Contracts

@router.get("/{user_address}/contracts", response_model=list[schemas.Contract])
async def get_user_contracts(user_address:str, db: Session = Depends(database.get_db)):
    # user = crud.get_user(db, user_address)
    contracts = crud.get_contracts_by_user(db, user_address)
    if not contracts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found."
            )
    return contracts

@router.get("/{address}", response_model=schemas.Contract)
async def get_contract(address: str, db: Session = Depends(database.get_db)):
    contract = crud.get_contract(db, address)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract not found."
            )
    return contract


# Entrypoints

@router.get("/{contract_address}/entrypoints", response_model=list[schemas.Entrypoint])
async def get_entrypoints(contract_address: str, db: Session = Depends(database.get_db)):
    entrypoints = crud.get_entrypoints(db, contract_address)
    return entrypoints

@router.get("/{contract_address}/entrypoints/{name}", response_model=schemas.Entrypoint)
async def get_entrypoint(contract_address: str, name: str, db: Session = Depends(database.get_db)):
    entrypoint = crud.get_entrypoint(db, contract_address, name)
    if not entrypoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entrypoint not found."
            )
    return entrypoint


### --- WIP

@router.post('/contracts')
async def create_contract(contract: Contract):
  user = database.find_user_by_address(contract.owner_address)
  if (len(user) == 0):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found."
            )
  new_contract = database.add_contract()
  return {"contract":None}