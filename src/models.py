from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base


class User(Base):
  __tablename__ = "users"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(String)
  address = Column(String, unique=True)

  contracts = relationship("Contract", back_populates="owner")

class Credit(Base):
  __tablename__ = "credits"

  id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4)
  amount = Column(Integer)
  owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

class Contract(Base):
  __tablename__ = "contracts"
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(String)
  address = Column(String, unique=True)
  credit_id = Column(UUID(as_uuid=True), ForeignKey("credits.id"))
  owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

  owner = relationship("User", back_populates="contracts")
  entrypoints = relationship("Entrypoint", back_populates="contract")

class Entrypoint(Base):
  __tablename__ = "entrypoints"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(String)
  is_enabled = Column(Boolean)
  contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id'))

  contract = relationship("Contract", back_populates='entrypoints')