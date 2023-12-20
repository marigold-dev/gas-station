from pydantic import BaseModel, UUID4
from typing import List, Any


# Users
class UserBase(BaseModel):
    address: str


class User(UserBase):
    id: UUID4
    name: str
    withdraw_counter: int


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


class CreditUpdate(BaseModel):
    id: UUID4
    amount: int
    operation_hash: str
    owner_id: str


class CreditWithdraw(BaseModel):
    id: UUID4
    amount: int
    withdraw_counter: int
    micheline_signature: str

    def to_micheline_pair(self):
        return [
            {"string": self.id},
            {"int": self.withdraw_counter},
            {"int": self.amount},
        ]


class WithdrawResponse(BaseModel):
    id: UUID4
    operation_hash: str


class WithdrawCounter(BaseModel):
    counter: int


# Contracts
class ContractBase(BaseModel):
    address: str
    owner_id: UUID4


class Contract(ContractBase):
    id: UUID4
    name: str
    entrypoints: List[Entrypoint]
    credit: Credit
    max_calls_per_month: int


class ContractCreation(ContractBase):
    name: str
    entrypoints: List[EntrypointCreation]
    credit_id: UUID4


# Operations
class UnsignedCall(BaseModel):
    """Data sent when posting an operation. The sender is mandatory."""

    sender_address: str
    operations: list[dict[str, Any]]


class SignedCall(BaseModel):
    """Data sent when posting an operation. The signature"""

    sender_key: str
    operations: list[dict[str, Any]]
    signature: str
    micheline_type: Any


class CreateOperation(BaseModel):
    contract_id: str
    entrypoint_id: str
    hash: str
    status: str


class UpdateMaxCallsPerMonth(BaseModel):
    max_calls: int
