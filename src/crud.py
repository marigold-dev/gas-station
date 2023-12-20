import datetime
from typing import Optional, List
from psycopg2.errors import UniqueViolation
from pydantic import UUID4
from sqlalchemy.orm import Session

from .utils import (
    ContractAlreadyRegistered,
    ContractNotFound,
    CreditNotFound,
    EntrypointNotFound,
    UserNotFound,
)
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
        return db.query(models.User).filter(models.User.address == address).one()
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
    return (
        db.query(models.Contract).filter(models.Contract.credit_id == credit_id).all()
    )


def get_contract_by_address(db: Session, address: str):
    """
    Return a models.Contract or raise ContractNotFound exception
    """
    try:
        return (
            db.query(models.Contract).filter(models.Contract.address == address).one()
        )
    except NoResultFound as e:
        raise ContractNotFound() from e


def get_contract(db: Session, contract_id: str):
    """
    Return a models.Contract or raise ContractNotFound exception
    """
    db_contract: Optional[models.Contract] = db.query(models.Contract).get(contract_id)
    if db_contract is None:
        raise ContractNotFound()
    return db_contract


def get_entrypoints(
    db: Session, contract_address_or_id: str
) -> List[models.Entrypoint]:
    """
    Return a list of models.Contract or raise ContractNotFound exception
    """
    if contract_address_or_id.startswith("KT"):
        contract = get_contract_by_address(db, contract_address_or_id)
    else:
        contract = get_contract(db, contract_address_or_id)
    return contract.entrypoints


def get_entrypoint(db: Session, contract_address_or_id: str, name: str):
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
    try:
        contract = get_contract_by_address(db, contract.address)
        raise ContractAlreadyRegistered(f"Contract {contract.address} already added.")
    except ContractNotFound:
        c = {k: v for k, v in contract.model_dump().items() if k not in ["entrypoints"]}
        db_contract = models.Contract(**c)
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        db_entrypoints = [
            models.Entrypoint(**e.model_dump(), contract_id=db_contract.id)
            for e in contract.entrypoints
        ]
        db.add_all(db_entrypoints)
        db.commit()
        return db_contract


def update_entrypoints(db: Session, entrypoints: list[schemas.EntrypointUpdate]):
    for e in entrypoints:
        db.query(models.Entrypoint).filter(models.Entrypoint.id == e.id).update(
            {"is_enabled": e.is_enabled}
        )
    db.commit()
    entrypoints_ids = list(map(lambda e: e.id, entrypoints))
    return (
        db.query(models.Entrypoint)
        .filter(models.Entrypoint.id.in_(entrypoints_ids))
        .all()
    )


def get_user_credits(db: Session, user_id: str):
    """
    Get credits from a user.
    """
    db_credits = db.query(models.Credit).filter(models.Credit.owner_id == user_id).all()
    return db_credits


def update_user_withdraw_counter(db: Session, user_id: str, withdraw_counter: int):
    try:
        db_user: Optional[models.User] = db.query(models.User).get(user_id)
        if db_user is None:
            raise UserNotFound()

        db.query(models.User).filter(models.User.id == user_id).update(
            {"withdraw_counter": withdraw_counter}
        )

        db.commit()
        return db_user.withdraw_counter
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
        db_credit: Optional[models.Credit] = db.query(models.Credit).get(
            credit_update.id
        )
        if db_credit is None:
            raise CreditNotFound()
        db.query(models.Credit).filter(models.Credit.id == credit_update.id).update(
            {"amount": db_credit.amount + amount}
        )
        db.commit()
        return db_credit
    except NoResultFound as e:
        raise CreditNotFound() from e


def update_credits_from_contract_address(db: Session, amount: int, address: str):
    try:
        db_contract: Optional[models.Credit] = (
            db.query(models.Contract)
            .filter(models.Contract.address == address)
            .one_or_none()
        )
        if db_contract is None:
            raise ContractNotFound()
        db.query(models.Credit).filter(
            models.Credit.id == db_contract.credit_id
        ).update({"amount": db_contract.credit.amount + amount})
        db.commit()
        return db_contract.credit
    except NoResultFound as e:
        raise CreditNotFound() from e


def get_credits(db: Session, uuid: UUID4):
    """
    Return a models.Credit or raise UserNotFound exception
    """
    db_credit = db.query(models.Credit).get(uuid)
    if db_credit is None:
        raise CreditNotFound()
    return db_credit


def get_credits_from_contract_address(db: Session, contract_address: str):
    try:
        db_contract = (
            db.query(models.Contract)
            .filter(models.Contract.address == contract_address)
            .one_or_none()
        )
        if db_contract is None:
            raise ContractNotFound()
        db_credit = (
            db.query(models.Credit)
            .filter(models.Credit.id == db_contract.credit_id)
            .one_or_none()
        )
        if db_credit is None:
            raise CreditNotFound()
        return db_credit
    except NoResultFound as e:
        raise ContractNotFound() from e


def create_operation(db: Session, operation: schemas.CreateOperation):
    db_operation = models.Operation(
        **{
            "contract_id": operation.contract_id,
            "entrypoint_id": operation.entrypoint_id,
            "hash": operation.hash,
            "status": operation.status,
        }
    )
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


def update_amount_operation(db: Session, hash: str, amount: int):
    db.query(models.Operation).filter(models.Operation.hash == hash).update(
        {"cost": amount}
    )
    db.commit()


def get_operations_by_contracts_per_month(db: Session, contract_id):
    first_day_of_month = datetime.datetime.today().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    db_operations = (
        db.query(models.Operation)
        .filter(models.Operation.contract_id == contract_id)
        .filter(models.Operation.created_at >= first_day_of_month)
        .all()
    )
    return db_operations


def get_max_calls_per_month_by_contract_address(db: Session, contract_id):
    contract = get_contract(db, contract_id)
    return contract.max_calls_per_month


def update_max_calls_per_month_condition(db: Session, max_calls: int, contract_id):
    db_contract = get_contract(db, contract_id)
    db.query(models.Contract).filter(models.Contract.id == contract_id).update(
        {"max_calls_per_month": max_calls}
    )
    db.commit()
    # db_contract.refresh()
    return db_contract
