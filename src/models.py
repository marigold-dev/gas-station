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
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.utils import ConditionType
from .database import Base
import datetime


# ------- USER ------- #
class User(Base):
    __tablename__ = "users"

    def __repr__(self):
        return "User(id='{}', name='{}', address='{}', counter='{}')".format(
            self.id, self.name, self.address, self.withdraw_counter
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    address = Column(String, unique=True)
    withdraw_counter = Column(Integer, default=0)

    contracts = relationship("Contract", back_populates="owner")
    credits = relationship("Credit", back_populates="owner")


# ------- CONTRACT ------- #
class Contract(Base):
    __tablename__ = "contracts"

    def __repr__(self):
        return "Contract(id='{}', name='{}', address='{}')".format(
            self.id, self.name, self.address
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    address = Column(String, unique=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    credit_id = Column(UUID(as_uuid=True), ForeignKey("credits.id"))
    max_calls_per_month = Column(
        Integer, default=-1
    )  # TODO must be > 0 ; -1 means disabled

    owner = relationship("User", back_populates="contracts")
    entrypoints = relationship("Entrypoint", back_populates="contract")
    credit = relationship("Credit", back_populates="contracts")
    operations = relationship("Operation", back_populates="contract")


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


# ------- CREDITS ------- #


class Credit(Base):
    __tablename__ = "credits"

    def __repr__(self):
        return "Credit(id='{}', amount='{}', owner_id='{}')".format(
            self.id, self.amount, self.owner_id
        )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Integer, default=0)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    owner = relationship("User", back_populates="credits")
    contracts = relationship("Contract", back_populates="credit")


# ------- OPERATIONS ------- #


class Operation(Base):
    __tablename__ = "operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost = Column(Integer)
    user_address = Column(String)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    entrypoint_id = Column(UUID(as_uuid=True), ForeignKey("entrypoints.id"))
    hash = Column(String)
    status = Column(String)  # TODO Enum
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow())

    contract = relationship("Contract", back_populates="operations")
    entrypoint = relationship("Entrypoint", back_populates="operations")


# ------- CONDITIONS ------- #


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(ConditionType))
    sponsee_address = Column(
        String,
        CheckConstraint(
            "(type = 'MAX_CALLS_PER_SPONSEE') = (sponsee_address IS NOT NULL)",
            name="sponsee_address_not_null_constraint",
        ),
        nullable=True,
    )
    contract_id = Column(
        UUID(as_uuid=True),
        CheckConstraint(
            "(type = 'MAX_CALLS_PER_ENTRYPOINT') = (contract_id IS NOT NULL)",
            name="contract_id_not_null_constraint",
        ),
        ForeignKey("contracts.id"),
        nullable=True,
    )
    entrypoint_id = Column(
        UUID(as_uuid=True),
        CheckConstraint(
            "(type = 'MAX_CALLS_PER_ENTRYPOINT') = (entrypoint_id IS NOT NULL)",
            name="entrypoint_id_not_null_constraint",
        ),
        ForeignKey("entrypoints.id"),
        nullable=True,
    )
    vault_id = Column(UUID(as_uuid=True), ForeignKey("credits.id"), nullable=False)
    max = Column(Integer, nullable=False)
    current = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.datetime.utcnow(), nullable=False
    )

    contract = relationship("Contract", back_populates="conditions")
    entrypoint = relationship("Entrypoint", back_populates="conditions")
    vault = relationship("Credits", back_populates="conditions")
