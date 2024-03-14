import datetime
import enum
from pydantic import BaseModel, UUID4
from typing import List, Any, Optional


# -- UTILITY TYPES --
class ConditionType(enum.Enum):
    # Max number of calls to a given entrypoint, for all sponsee
    MAX_CALLS_PER_ENTRYPOINT = "MAX_CALLS_PER_ENTRYPOINT"
    # Max number of calls per sponsee per contract
    MAX_CALLS_PER_SPONSEE = "MAX_CALLS_PER_SPONSEE"


# Sponsors
class SponsorBase(BaseModel):
    tezos_address: str


class Sponsor(SponsorBase):
    id: UUID4
    name: str
    withdraw_counter: int


class SponsorCreation(SponsorBase):
    name: str


# Sonsor APIs
class SponsorAPICreation(BaseModel):
    sponsor_id: UUID4
    api_url: str
    public_key: str


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
    sender_address: str
    contract_id: str
    entrypoint_id: str
    hash: str
    status: str


# Conditions
class UpdateMaxCallsPerMonth(BaseModel):
    max_calls: int


class CreateCondition(BaseModel):
    type: ConditionType
    contract_id: Optional[UUID4] = None
    entrypoint_id: Optional[UUID4] = None
    vault_id: UUID4
    max: int


class CreateMaxCallsPerEntrypointCondition(BaseModel):
    contract_id: UUID4
    entrypoint_id: UUID4
    vault_id: UUID4
    max: int


class CreateMaxCallsPerSponseeCondition(BaseModel):
    contract_id: UUID4
    vault_id: UUID4
    max: int


class CheckConditions(BaseModel):
    sponsee_address: str
    contract_id: UUID4
    entrypoint_id: UUID4
    vault_id: UUID4


class ConditionBase(BaseModel):
    vault_id: UUID4
    contract_id: UUID4
    max: int
    current: int
    type: ConditionType
    id: UUID4
    created_at: datetime.datetime


class MaxCallsPerEntrypointCondition(ConditionBase):
    entrypoint_id: UUID4
