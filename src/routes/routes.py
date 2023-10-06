from src import database as db
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel


router = APIRouter()

class User(BaseModel):
    user_name: str
    user_address: str | None


@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get("/{user_address}/contracts")
async def get_user_contracts(user_address):
    user = db.find_user(user_address)
    if (len(user) == 0):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found."
            )
    contracts = db.find_contracts_by_user(user_address)
    return {"contracts": contracts}

@router.post('/users')
async def create_user(user: User):
  new_inserted = db.add_user(user.user_address, user.user_name)
  print(new_inserted)
  return {"user": new_inserted}
