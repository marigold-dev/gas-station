from pydantic import BaseModel, UUID4
from typing import List


# Users
class UserBase(BaseModel):
    address: str

class User(UserBase):
  id: UUID4
  name: str
  credits: int

class UserCreation(UserBase):
    name: str

class UserUpdateCredit(BaseModel):
  address: str
  credits: int

# Entrypoints
class EntrypointBase(BaseModel):
    name: str
    contract_id: UUID4
    is_enabled: bool

class Entrypoint(EntrypointBase):
  id: UUID4

class EntrypointCreation(BaseModel):
  name: str
  is_enabled: bool

# Contracts
class ContractBase(BaseModel):
  address: str
  owner_id: UUID4

class Contract(ContractBase):
  id: UUID4
  name: str
  entrypoints: List[Entrypoint]

class ContractCreation(ContractBase):
  name: str
  entrypoints: List[EntrypointCreation]