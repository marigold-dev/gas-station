from typing import Optional, List
from pydantic import UUID4
from sqlalchemy.orm import Session

from src.utils import ContractNotFound, CreditNotFound
from src.utils import EntrypointNotFound, UserNotFound
from . import models, schemas
from sqlalchemy.exc import NoResultFound


def get_user(db: Session, uuid: UUID4):
    """
    Return a models.User or raise UserNotFound exception
    """
    try:
        return db.query(models.User).get(uuid)
    except NoResultFound as e:
        raise UserNotFound() from e


def get_user_by_address(db: Session, address: str):
    """
    Return a models.User or raise UserNotFound exception
    """
    try:
        return db.query(models.User).filter(
            models.User.address == address).one()
    except NoResultFound as e:
        raise UserNotFound() from e


def create_user(db: Session, user: schemas.UserCreation):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_contracts_by_user(db: Session, user_address: str):
    """
    Return a list of models.Contracts or raise UserNotFound exception
    """
    user = get_user_by_address(db, user_address)
    return user.contracts


def get_contracts_by_credit(db: Session, credit_id: str):
    """
    Return a list of models.Contracts or raise UserNotFound exception
    """
    return db.query(models.Contract).filter(
        models.Contract.credit_id == credit_id).all()


def get_contract(db: Session, address: str):
    """
    Return a models.Contract or raise ContractNotFound exception
    """
    try:
        return db.query(models.Contract).filter(
            models.Contract.address == address
        ).one()
    except NoResultFound as e:
        raise ContractNotFound() from e


def get_entrypoints(db: Session,
                    contract_address: str) -> List[models.Entrypoint]:
    """
    Return a list of models.Contract or raise ContractNotFound exception
    """
    contract = get_contract(db, contract_address)
    return contract.entrypoints


def get_entrypoint(db: Session, contract_address: str,
                   name: str) -> Optional[models.Entrypoint]:
    """
    Return a models.Entrypoint or raise EntrypointNotFound exception
    """
    entrypoints = get_entrypoints(db, contract_address)
    entrypoint = [e for e in entrypoints if e.name == name]  # type: ignore
    if len(entrypoint) == 0:
        raise EntrypointNotFound()
    return entrypoint[0]


def create_contract(db: Session, contract: schemas.ContractCreation):
    # TODO rewrite this with transaction or something else better
    c = {k: v
         for k, v in contract.model_dump().items()
         if k not in ['entrypoints']}
    db_contract = models.Contract(**c)
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    db_entrypoints = [models.Entrypoint(**e.model_dump(),
                                        contract_id=db_contract.id)
                      for e in contract.entrypoints]
    db.add_all(db_entrypoints)
    db.commit()
    return db_contract


def update_entrypoints(db: Session,
                       entrypoints: list[schemas.EntrypointUpdate]):
    for e in entrypoints:
        db.query(models.Entrypoint).filter(
            models.Entrypoint.id == e.id
        ).update({'is_enabled': e.is_enabled})
    db.commit()
    entrypoints_ids = list(map(lambda e: e.id, entrypoints))
    return db.query(models.Entrypoint).filter(
        models.Entrypoint.id.in_(entrypoints_ids)
    ).all()


def create_operation(db: Session, operation: schemas.CreateOperation):
    db_operation = models.Operation(
        **{"contract_id":  operation.contract_id,
           "entrypoint_id": operation.entrypoint_id}
    )
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


def update_operation(db: Session, operation_id: str, transaction_hash: str,
                     status: str):
    db.query(models.Operation).filter(
        models.Operation.id == operation_id
    ).update({'transaction_hash': transaction_hash, "status": status})
    db.commit()


def update_amount_operation(db: Session, hash: str, amount: int):
    db.query(models.Operation).filter(
        models.Operation.transaction_hash == hash
    ).update({'cost': amount})
    db.commit()


def get_user_credits(db: Session, user_id: str):
    """
    Get credits from a user.
    """
    db_credits = db.query(models.Credit).filter(models.Credit.owner_id == user_id).all()
    return db_credits


def create_credits(db: Session, credit: schemas.CreditCreation):
    """
    Creates credits for a given owner and returns a models.Credit.
    """
    try:
        # Check if the user exists
        _ = db.query(models.User).get(credit.owner_id)
        credit = models.Credit(**credit.model_dump())
        db.add(credit)
        db.commit()
        # db.refresh(credit)
        return credit
    except NoResultFound as e:
        raise UserNotFound() from e


def update_credits(db: Session, credit_update: schemas.CreditUpdate):
    """
    Update a credit row and return a models.Credit. \n
    Can raise a ContractNotFound exception or CreditNotFound exception.
    """
    try:
        amount = credit_update.amount
        db_credit: models.Credit | None = db.query(models.Credit).get(credit_update.id)
        if db_credit is None:
            raise CreditNotFound()
        db.query(models.Credit).filter(models.Credit.id == credit_update.id).update({'amount': db_credit.amount + amount})
        db.commit()
        return db_credit
    except NoResultFound as e:
        raise CreditNotFound() from e
