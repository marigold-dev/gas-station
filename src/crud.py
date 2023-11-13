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
    db_user: Optional[models.User] = db.query(models.User).get(uuid)
    if db_user is None:
        raise UserNotFound()
    return db_user


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


def get_contract_by_address(db: Session, address: str):
    """
    Return a models.Contract or raise ContractNotFound exception
    """
    try:
        return db.query(models.Contract).filter(
            models.Contract.address == address
        ).one()
    except NoResultFound as e:
        raise ContractNotFound() from e


def get_contract(db: Session, contract_id: str):
    """
    Return a models.Contract or raise ContractNotFound exception
    """
    try:
        return db.query(models.Contract).get(contract_id)
    except NoResultFound as e:
        raise ContractNotFound() from e


def get_entrypoints(
    db: Session,
    contract_address_or_id: str
) -> List[models.Entrypoint]:
    """
    Return a list of models.Contract or raise ContractNotFound exception
    """
    if contract_address_or_id.startswith("KT"):
        contract = get_contract_by_address(db, contract_address_or_id)
    else:
        contract = get_contract(db, contract_address_or_id)
    return contract.entrypoints


def get_entrypoint(db: Session,
                   contract_address_or_id: str,
                   name: str) -> Optional[models.Entrypoint]:
    """
    Return a models.Entrypoint or raise EntrypointNotFound exception
    """
    entrypoints = get_entrypoints(db, contract_address_or_id)
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


def get_user_credits(db: Session, user_id: str):
    """
    Get credits from a user.
    """
    db_credits = db.query(models.Credit).filter(models.Credit.owner_id == user_id).all()
    return db_credits


def update_user_withdraw_counter(db: Session,
                                 user_id: str,
                                 withdraw_counter: int):
    try:
        db.query(models.User).filter(
            models.User.id == user_id
        ).update({"withdraw_counter": withdraw_counter})
        db.commit()
    except NoResultFound as e:
        raise UserNotFound from e


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
        db_credit: Optional[models.Credit] = db.query(models.Credit).get(credit_update.id)
        if db_credit is None:
            raise CreditNotFound()
        db.query(models.Credit).filter(models.Credit.id == credit_update.id).update({'amount': db_credit.amount + amount})
        db.commit()
        return db_credit
    except NoResultFound as e:
        raise CreditNotFound() from e


def update_credits_from_contract_address(db: Session, amount: int, address: str):
    try:
        db_contract: Optional[models.Credit] = db.query(models.Contract).filter(models.Contract.address == address).one_or_none()
        if db_contract is None:
            raise ContractNotFound()
        db.query(models.Credit).filter(models.Credit.id == db_contract.credit_id).update({'amount': db_contract.credit.amount + amount})
        db.commit()
        return db_contract.credit
    except NoResultFound as e:
        raise CreditNotFound() from e


def get_credits(db: Session, uuid: UUID4):
    """
    Return a models.Credit or raise UserNotFound exception
    """
    db_credit = db.query(models.Credit).get(uuid)
    if (db_credit is None):
        raise CreditNotFound()
    return db_credit


def get_credits_from_contract_address(db: Session, contract_address: str):
    try:
        db_contract = db.query(models.Contract).filter(
            models.Contract.address == contract_address
        ).one_or_none()
        if db_contract is None:
            raise ContractNotFound()
        print(db_contract)
        db_credit = db.query(models.Credit).filter(
            models.Credit.id == db_contract.credit_id
        ).one_or_none()
        if db_credit is None:
            raise CreditNotFound()
        return db_credit
    except NoResultFound as e:
        raise ContractNotFound() from e
