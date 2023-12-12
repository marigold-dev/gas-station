from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base


# ------- USER ------- #
class User(Base):
    __tablename__ = "users"

    def __repr__(self):
        return "User(id='{}', name='{}', address='{}')".format(
            self.id, self.name, self.address
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

    owner = relationship("User", back_populates="contracts")
    entrypoints = relationship("Entrypoint", back_populates="contract")
    credit = relationship("Credit", back_populates="contracts")


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
