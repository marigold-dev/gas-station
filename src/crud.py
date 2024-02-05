import datetime
from typing import Optional, List
from psycopg2.errors import UniqueViolation
from pydantic import UUID4
from sqlalchemy.orm import Session

from .utils import (
    ConditionAlreadyExists,
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


def check_user_is_new(db: Session, user_id: UUID4) -> bool:
    """
    Function to determine if a user is one of the last 4
    new users registered in the database.
    """
    try:
        # Get the last 4 users ordered by their registration data
        recent_users: List[models.User] = (
            db.query(models.User)
            .order_by(models.User.created_at.desc())
            .limit(4)
            .all()
        )
        # Check if the given user_id is among the last 4 users
        return any(user.id == user_id for user in recent_users)
    except UserNotFound:
        # If the user is not found, they are not among the newest users
        return False


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
        db.query(models.Contract).filter(
            models.Contract.credit_id == credit_id).all()
    )


def get_contract_by_address(db: Session, address: str):
    """
    Return a models.Contract or raise ContractNotFound exception
    """
    try:
        return (
            db.query(models.Contract).filter(
                models.Contract.address == address).one()
        )
    except NoResultFound as e:
        raise ContractNotFound() from e


def get_contract(db: Session, contract_id: str):
    """
    Return a models.Contract or raise ContractNotFound exception
    """
    db_contract: Optional[models.Contract] = db.query(
        models.Contract).get(contract_id)
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
        raise ContractAlreadyRegistered(
            f"Contract {contract.address} already added.")
    except ContractNotFound:
        c = {k: v for k, v in contract.model_dump().items() if k not in [
            "entrypoints"]}
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
    db_credits = db.query(models.Credit).filter(
        models.Credit.owner_id == user_id).all()
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
            "user_address": operation.user_address,
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


def check_calls_per_month(db, contract_id):
    max_calls = get_max_calls_per_month_by_contract_address(db, contract_id)
    # If max_calls is -1 means condition is disabled (NO LIMIT)
    if max_calls == -1:  # type: ignore
        return True
    nb_operations_already_made = get_operations_by_contracts_per_month(
        db, contract_id)
    return max_calls >= len(nb_operations_already_made)


def create_max_calls_per_contract_for_new_users_condition(
    db: Session, condition: schemas.CreateMaxCallsPerContractForNewUsersCondition
):
    """
    Creates a condition in the database that limits the
    maximum number of calls per users within a contract
    """
    # First checks if there is an existing condition with the same
    # user_id, contract and vault ID in the database, if the
    # maximum number of calls has not been reached.
    existing_condition = (
        db.query(models.Condition)
        .filter(models.Condition.user_id == condition.user_id)
        .filter(models.Condition.contract_id == condition.contract_id)
        .filter(models.Condition.vault_id == condition.vault_id)
        .filter(models.Condition.current < models.Condition.max)
        .one_or_none()
    )
    if existing_condition is not None:
        raise ConditionAlreadyExists(
            "A condition with maximum calls per contract for new users already exists and the maximum is not reached. Cannot create a new one."
        )
    # Creating a new condition
    db_condition = models.Condition(
        **{
            "type": schemas.ConditionType.MAX_CALLS_PER_CONTRACT_FOR_NEW_USERS,
            "contract_id": condition.contract_id,
            "user_id": condition.user_id,  # ID of the user
            "vault_id": condition.vault_id,
            "max": condition.max,  # maximum allowed number of calls for the user
            "current": 0,  # representing the current number of calls
        }
    )
    db.add(db_condition)
    db.commit()
    db.refresh(db_condition)
    return schemas.MaxCallsPerContractForNewUsersCondition(
        contract_id=db_condition.contract_id,
        user_id=db_condition.user_id,
        vault_id=db_condition.vault_id,
        max=db_condition.max,
        current=db_condition.current,
        type=db_condition.type,
        created_at=db_condition.created_at,
        id=db_condition.id,
    )


def create_max_calls_per_entrypoint_condition(
    db: Session, condition: schemas.CreateMaxCallsPerEntrypointCondition
):
    # If a condition still exists, do not create a new one
    existing_condition = (
        db.query(models.Condition)
        .filter(models.Condition.entrypoint_id == condition.entrypoint_id)
        .filter(models.Condition.contract_id == condition.contract_id)
        .filter(models.Condition.vault_id == condition.vault_id)
        .filter(models.Condition.current < models.Condition.max)
        .one_or_none()
    )
    if existing_condition is not None:
        raise ConditionAlreadyExists(
            "A condition with maximum calls per entrypoint already exists and the maximum is not reached. Cannot create a new one."
        )
    db_condition = models.Condition(
        **{
            "type": schemas.ConditionType.MAX_CALLS_PER_ENTRYPOINT,
            "contract_id": condition.contract_id,
            "entrypoint_id": condition.entrypoint_id,
            "vault_id": condition.vault_id,
            "max": condition.max,
            "current": 0,
        }
    )
    db.add(db_condition)
    db.commit()
    db.refresh(db_condition)
    return schemas.MaxCallsPerEntrypointCondition(
        contract_id=db_condition.contract_id,
        entrypoint_id=db_condition.entrypoint_id,
        vault_id=db_condition.vault_id,
        max=db_condition.max,
        current=db_condition.current,
        type=db_condition.type,
        created_at=db_condition.created_at,
        id=db_condition.id,
    )


def check_max_calls_per_contract_for_new_users(db: Session, contract_id: UUID4, user_id: UUID4, vault_id: UUID4):
    return (
        db.query(models.Condition)
        .filter(models.Condition.type == schemas.ConditionType.MAX_CALLS_PER_CONTRACT_FOR_NEW_USERS)
        .filter(models.Condition.contract_id == contract_id)
        .filter(models.Condition.user_id == user_id)
        .filter(models.Condition.vault_id == vault_id)
        .one_or_none()
    )


def check_max_calls_per_entrypoint(
    db: Session, contract_id: UUID4, entrypoint_id: UUID4, vault_id: UUID4
):
    return (
        db.query(models.Condition)
        .filter(models.Condition.type == schemas.ConditionType.MAX_CALLS_PER_ENTRYPOINT)
        .filter(models.Condition.contract_id == contract_id)
        .filter(models.Condition.entrypoint_id == entrypoint_id)
        .filter(models.Condition.vault_id == vault_id)
        .one_or_none()
    )


def check_conditions(db: Session, datas: schemas.CheckConditions):
    print(datas)
    contract_for_new_users_condition = check_max_calls_per_contract_for_new_users(
        db, datas.contract_id, datas.user_id, datas.vault_id
    )

    entrypoint_condition = check_max_calls_per_entrypoint(
        db, datas.contract_id, datas.entrypoint_id, datas.vault_id
    )

    # Checks if both conditions are none, mean that there are no conditions registered,
    # return true
    if contract_for_new_users_condition is None and entrypoint_condition is None:
        return True

    # Check either of the condition has been excedeed.
    # If either condition is not None and its current value is >= its max value, it return false,
    # indicating that the condition has been exceeded.
    if (
        contract_for_new_users_condition is not None
        and (contract_for_new_users_condition.current >= contract_for_new_users_condition.max)
    ) or (
        entrypoint_condition is not None
        and (entrypoint_condition.current >= entrypoint_condition.max)
    ):
        return False

    # Update conditions
    if contract_for_new_users_condition or entrypoint_condition:
        update_conditions(
            db, [c for c in [contract_for_new_users_condition, entrypoint_condition] if c])
    return True


def update_conditions(db: Session, conditions: List[models.Condition]):
    for condition in conditions:
        db.query(models.Condition).filter(models.Condition.id == condition.id).update(
            {"current": models.Condition.current + 1}
        )
        db.commit()


def get_conditions_by_vault(db: Session, vault_id: str):
    return (
        db.query(models.Condition).filter(
            models.Condition.vault_id == vault_id).all()
    )
