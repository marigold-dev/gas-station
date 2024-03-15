from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .schemas import ConditionType
from .database import Base
import datetime


# ------- SPONSOR CLASSES ------- #
# Sponsors
# - must have a tezos address, which they may use to provide credits
# - may have an API, to which user operations are transmitted, and
#   which may post these operations themselves, or just return a signed
#   receipt to the gas station (which then posts the operations itself)
# If the sponsor API returns the operation to the GS, then the sponsor must
# have deposited credits.
class SponsorAPI(Base):
    __tablename__ = "sponsor_apis"

    def __repr__(self):
        return "API(id='{}', url='{}')".format(
            self.id, self.url
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, unique=True)
    public_key = Column(String, nullable=False)


class Sponsor(Base):
    __tablename__ = "sponsors"

    def __repr__(self):
        return "Sponsor(id='{}', name='{}', address='{}', counter='{}')".format(
            self.id, self.name, self.tezos_address, self.withdraw_counter
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    tezos_address = Column(String, unique=True)
    withdraw_counter = Column(Integer, default=0)
    api_id = Column(UUID(as_uuid=True), ForeignKey("sponsor_apis.id"))
    contracts = relationship("Contract", back_populates="owner")
    credits = relationship("Credit", back_populates="owner")
    sponsor_api = relationship("SponsorAPI")


# ------- CONTRACT ------- #
# TODO: contract sponsored by several owners
# Do not require contracts to be tied to a specific credit
class Contract(Base):
    __tablename__ = "contracts"

    def __repr__(self):
        return "Contract(id='{}', name='{}', address='{}')".format(
            self.id, self.name, self.address
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    address = Column(String, unique=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("sponsors.id"))
    credit_id = Column(UUID(as_uuid=True), ForeignKey("credits.id"))
    max_calls_per_month = Column(
        Integer, default=-1
    )  # TODO must be > 0 ; -1 means disabled

    owner = relationship("Sponsor", back_populates="contracts")
    entrypoints = relationship("Entrypoint", back_populates="contract")
    credit = relationship("Credit", back_populates="contracts")
    operations = relationship("Operation", back_populates="contract")
    conditions = relationship("Condition", back_populates="contract")


# ------- ENTRYPOINT ------- #
class Entrypoint(Base):
    __tablename__ = "entrypoints"

    def __init__(self, name, is_enabled, contract_id):
        self.contract_id = contract_id
        self.name = name
        self.is_enabled = is_enabled

    def __repr__(self):
        return "Entrypoint(contract_id='{}', name='{}')".format(
            self.contract_id, self.name
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    is_enabled = Column(Boolean)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"))

    contract = relationship("Contract", back_populates="entrypoints")
    operations = relationship("Operation", back_populates="entrypoint")
    conditions = relationship("Condition", back_populates="entrypoint")


# ------- CREDITS ------- #


class Credit(Base):
    __tablename__ = "credits"

    def __repr__(self):
        return "Credit(id='{}', amount='{}', owner_id='{}')".format(
            self.id, self.amount, self.owner_id
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Integer, default=0)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("sponsors.id"))

    owner = relationship("Sponsor", back_populates="credits")
    contracts = relationship("Contract", back_populates="credit")
    conditions = relationship("Condition", back_populates="vault")


# ------- OPERATIONS ------- #


class Operation(Base):
    __tablename__ = "operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost = Column(Integer)
    sender_address = Column(String)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    entrypoint_id = Column(UUID(as_uuid=True), ForeignKey("entrypoints.id"))
    hash = Column(String)
    status = Column(String)  # TODO Enum
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="operations")
    entrypoint = relationship("Entrypoint", back_populates="operations")


# ------- CONDITIONS ------- #


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(ConditionType))
    contract_id = Column(
        UUID(as_uuid=True),
        CheckConstraint(
            "(type = 'MAX_CALLS_PER_ENTRYPOINT' or type = \
            'MAX_CALLS_PER_SPONSEE') = (contract_id IS NOT NULL)",
            name="contract_id_not_null_constraint",
        ),
        ForeignKey("contracts.id"),
        nullable=True,
    )
    entrypoint_id = Column(
        UUID(as_uuid=True),
        CheckConstraint(
            "(type = 'MAX_CALLS_PER_ENTRYPOINT') = \
            (entrypoint_id IS NOT NULL)",
            name="entrypoint_id_not_null_constraint",
        ),
        ForeignKey("entrypoints.id"),
        nullable=True,
    )
    vault_id = Column(UUID(as_uuid=True), ForeignKey("credits.id"), nullable=False)
    max = Column(Integer, nullable=False)
    current = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active = Column(Boolean, nullable=False)
    contract = relationship("Contract", back_populates="conditions")
    entrypoint = relationship("Entrypoint", back_populates="conditions")
    vault = relationship("Credit", back_populates="conditions")
