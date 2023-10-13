from typing import Optional
from sqlalchemy.orm import Session
from . import models, schemas


def get_user(db: Session, address: str):
    return db.query(models.User).filter(models.User.address == address).first()

def create_user(db: Session, user: schemas.UserCreation):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_contracts_by_user(db: Session, user_address: str):
    user = get_user(db, user_address)
    if not user:
        return None
    return user.contracts


def get_contract(db: Session, address: str):
    return db.query(models.Contract).filter(models.Contract.address == address).first()


def get_entrypoints(db: Session, contract_address: str):
    contract = get_contract(db, contract_address)
    return contract.entrypoints if contract else []

def get_entrypoint(db: Session, contract_address: str, name: str) -> Optional[models.Entrypoint]:
    entrypoints = get_entrypoints(db, contract_address)
    entrypoint = list(filter(lambda e: e.name == name, entrypoints))
    if len(entrypoint) == 0:
        return None
    return entrypoint[0]

def create_contract(db: Session, contract: schemas.ContractCreation):
    c = {k:v for k,v in contract.model_dump().items() if k not in ['entrypoints']}
    db_contract = models.Contract(**c)
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    db_entrypoints =list(map(lambda e: models.Entrypoint(**e.model_dump(), contract_id=db_contract.id), contract.entrypoints))
    db.add_all(db_entrypoints)
    db.commit()
    return db_contract

def update_credits(db: Session, user_update: schemas.UserUpdateCredit):
    print(user_update)
    db_user = db.query(models.User).filter(models.User.address == user_update.address).first()
    if (db_user):
        db.query(models.User).filter(models.User.address == user_update.address).update({'credits': db_user.credits + user_update.credits})
        db.commit()
    return db.query(models.User).filter(models.User.address == user_update.address).first()

def update_entrypoints(db: Session, entrypoints: list[schemas.EntrypointUpdate]):
    for e in entrypoints:
        db.query(models.Entrypoint).filter(models.Entrypoint.id == e.id).update({'is_enabled': e.is_enabled})
    db.commit()
    entrypoints_ids = list(map(lambda e: e.id, entrypoints))
    return db.query(models.Entrypoint).filter(models.Entrypoint.id.in_(entrypoints_ids)).all()

def create_operation(db: Session, operation: schemas.CreateOperation):
    db_operation = models.Operation(**{"contract_id":  operation.contract_id, "entrypoint_id": operation.entrypoint_id})
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation

def update_operation(db: Session, operation_id: str, transaction_hash: str, status: str):
    db_op = db.query(models.Operation).filter(models.Operation.id == operation_id).update({'transaction_hash': transaction_hash, "status": status})
    db.commit()

def update_amount_operation(db: Session,hash: str, amount: int):
    db_op = db.query(models.Operation).filter(models.Operation.transaction_hash == hash).update({'cost': amount})
    db.commit()