from pydantic import BaseModel, UUID4
from typing import List, Any


# Users
class UserBase(BaseModel):
    address: str

class User(UserBase):
  id: UUID4
  name: str

class UserCreation(UserBase):
    name: str

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

class EntrypointUpdate(BaseModel):
  id: UUID4
  is_enabled: bool

# Credits
class Credit(BaseModel):
  id: UUID4
  amount: int
  owner_id: UUID4

class CreditCreation(BaseModel):
  owner_id: UUID4

class CreditUpdate(Credit):
    operation_hash: str

# Contracts
class ContractBase(BaseModel):
  address: str
  owner_id: UUID4

class Contract(ContractBase):
  id: UUID4
  name: str
  entrypoints: List[Entrypoint]
  credit: Credit

class ContractCreation(ContractBase):
  name: str
  entrypoints: List[EntrypointCreation]
  credit_id: UUID4

# Operations
# TODO: right now the sender isn't checked, as we use permits anyway
class CallData(BaseModel):
    sender: str
    operations: list[dict[str, Any]]

class CreateOperation(BaseModel):
  contract_id: str
  entrypoint_id: str
