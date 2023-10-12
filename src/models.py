from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base

# ------- USER ------- #
class User(Base):
  __tablename__ = "users"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(String)
  address = Column(String, unique=True)
  credits = Column(Integer, default=0)

  contracts = relationship("Contract", back_populates="owner")



# ------- CONTRACT ------- #
class Contract(Base):
  __tablename__ = "contracts"

  def __repr__(self):
    return "Contract(id='{}', name='{}', address='{}')".format(self.id, self.name, self.address)


  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(String)
  address = Column(String, unique=True)
  owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

  owner = relationship("User", back_populates="contracts")
  entrypoints = relationship("Entrypoint", back_populates="contract")
  operations = relationship("Operation", back_populates='contract')



# ------- ENTRYPOINT ------- #
class Entrypoint(Base):
  __tablename__ = "entrypoints"

  def __init__(self, name, is_enabled, contract_id):
    self.contract_id = contract_id
    self.name = name
    self.is_enabled = is_enabled

  def __repr__(self):
    return "Entrypoint(contract_id='{}', name='{}')".format(self.contract_id, self.name)

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(String)
  is_enabled = Column(Boolean)
  contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id'))

  contract = relationship("Contract", back_populates='entrypoints')
  operations = relationship("Operation", back_populates='entrypoint')


# ------- OPERATION ------- #
class Operation(Base):
  __tablename__ = "operations"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  cost = Column(Integer)
  contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id'))
  entrypoint_id = Column(UUID(as_uuid=True), ForeignKey('entrypoints.id'))
  transaction_hash = Column(String)
  status = Column(String) # TODO ENUM

  contract = relationship("Contract", back_populates="operations")
  entrypoint = relationship("Entrypoint", back_populates="operations")