from pydantic import BaseModel, UUID4


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

# Contracts
class ContractBase(BaseModel):
  address: str
  owner_id: UUID4

class Contract(ContractBase):
  id: UUID4
  name: str
  credit_id: UUID4


