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


# Database operations:
# Function like: get_user, get_contract, get_entrypoints,
# get_operations_by_contracts_per_month
# etc. retrieve data from the database based on specified conditions
def get_user(db: Session, uuid: UUID4):
    """
    Retrieve a user from the database by UUID
    Args:
        db (Session): SQLAlchemy database session.
        uuid (UUID4): UUID of the user to retrieve.
    Return:
        models.User: Retrieve user.
    Raises:
        UserNotFound: If user with the provided UUID does not exists.
    """
    db_user: Optional[models.User] = db.query(models.User).get(uuid)
    if db_user is None:
        raise UserNotFound()
    return db_user


def get_user_by_address(db: Session, address: str):
    """
    Retrieve a user from the database by address.
    Args:
        db (Session): SQLAlchemy database session.
        address (str): Address of the user to retrieve.
    Return:
        models.User: Retrieve user.
    Raises:
        UserNotFound: If user with the provided address does not exists.
    """
    try:
        return db.query(models.User).filter(models.User.address == address).one()
    except NoResultFound as e:
        raise UserNotFound() from e


def get_contracts_by_user(db: Session, user_address: str):
    """
    Retrieve contracts associated with a user from the database.
    Args:
        db (Session): database session.
        user_address (str): Address of the user.
    Returns:
        List[models.Contracts]: List of contracts associated with the user.
    Raise:
        UserNotFound: If user with the provided address does not exists.
    """
    user = get_user_by_address(db, user_address)
    return user.contracts


def get_contracts_by_credit(db: Session, credit_id: str):
    """
    Retrieve contracts associated with a credit from the database.
    Args:
        db (Session): database session.
        create_id (str): ID of the credit.
    Returns:
        List[models.Contracts]: List of contracts associated with the create
    """
    return (
        db.query(models.Contract).filter(
            models.Contract.credit_id == credit_id).all()
    )


def get_contract_by_address(db: Session, address: str):
    """
    Retrieve a contract from the database by address.
    Args:
        db (Session): database session.
        address (str): Address of the contract to retrieve.
    Returns:
        [models.Contract]: Retrieved contract.
    Raises:
         ContractNotFound: If contract with the provided address does not exists.
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
    Retrieve a contract from the database by ID.
    Args:
        db (Session): database session
        contract_id (str): ID of the contract to retrieve.
    Returns:
        models.Contract: Retrieved contract.
    Raises:
        ContractNotFound: If contract with the provided ID does not exists.
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
     Retrieve entrypoints of a contract from the database.
    Args:
        db (Session): database session.
        contract_address_or_id (str): Address or ID of the contract.
    Returns:
        List[models.Entrypoint]: List of entrypoints of the contract.
    Raises:
        ContractNotFound: If contract with the provided address or ID does not exists.
    """
    if contract_address_or_id.startswith("KT"):
        contract = get_contract_by_address(db, contract_address_or_id)
    else:
        contract = get_contract(db, contract_address_or_id)
    return contract.entrypoints


def get_entrypoint(db: Session, contract_address_or_id: str, name: str):
    """
    Retrieve entrypoints of a contract from the database.
    Args:
        db (Session): database session.
        contract_address_or_id (str): Address or ID of the contract.
        name (str): Name of the entrypoint to retrieve.
    Returns:
        models.Entrypoint: Retrieved entrypoint.
    Raises:
        EntrypointNotFound: If entrypoint with the provided name does not exists.
    """
    entrypoints = get_entrypoints(db, contract_address_or_id)
    entrypoint = [e for e in entrypoints if e.name == name]  # type: ignore
    if len(entrypoint) == 0:
        raise EntrypointNotFound()
    return entrypoint[0]


def get_user_credits(db: Session, user_id: str):
    """
    Retrieve credits associated with a user from the database
    Args:
        db (Session): database session.
        user_id (str): ID of the user.
    Returns:
        List[models.Credit]: List of credits associated with the user.
    """
    db_credits = db.query(models.Credit).filter(
        models.Credit.owner_id == user_id).all()
    return db_credits


def get_credits(db: Session, uuid: UUID4):
    """
    Retrieve a credit from the database by UUID4.
    Args:
        db (Session): database session
        uuid (UUID4): UUID of the credit to retrieve.
    Returns:
        models.Credit: Retrieved credit.
    Raises:
        UserNotFound: If credit with the provided UUID does not exists.
    """
    db_credit = db.query(models.Credit).get(uuid)
    if db_credit is None:
        raise CreditNotFound()
    return db_credit


def get_credits_from_contract_address(db: Session, contract_address: str):
    """
    Retrieve credits associated with a contract from the database.
    Args:
        db (Session): database session
        contract_address (str): Address of the contract;
    Returns:
        models.Credit: Retrieved credits.
    Raises:
        ContractNotFound: If contract with the provided address does not exists.
        CreditNotFound: If credit associated with the contract does not exists.
    """
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


def get_operations_by_contracts_per_month(db: Session, contract_id):
    """
    Retrieve operations associated with a contract for the current month from the database.
    Args:
        db (Session): database session.
        contract_id (str): ID of the contract.
    Returns:
        List[models.Operation]: List of operations associated with the contract for the current month.
    """
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
    """
    Retrieve maximum calls per month allowed for a contract from the database.
    Args:
        db (Session): database session.
        contract_id (str): ID of the contract.
    Returns:
        int: Maximum calls per month allowed for the contract.
    """
    contract = get_contract(db, contract_id)
    return contract.max_calls_per_month


def get_conditions_by_vault(db: Session, vault_id: str):
    """
    Retrieve conditions associated with a vault from the database.
    Args:
        db (Session): database session.
        vault_id (str): ID of the vault.
    Returns:
        List[models.Condition]: List of conditions associated with the vault.
    """
    return (
        db.query(models.Condition).filter(
            models.Condition.vault_id == vault_id).all()
    )

# Functions for creating news records in the database


def create_user(db: Session, user: schemas.UserCreation):
    """
    Create a new user record in the database.
    Args:
        db (Session): database session.
        user (schemas.UserCreation): User creation data.
    Returns:
        models.User: created user.
    """
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_contract(db: Session, contract: schemas.ContractCreation):
    """
    Create a new contract record in the database.
    Args:
        db (Session): database session.
        contract (schemas.ContractCreation): Contract creation data.
    Returns:
        models.Contract: Created contract.
    Raises:
        ContractAlreadyRegistered: If contract with the provided address is
        already registered.
    """
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


def create_credits(db: Session, credit: schemas.CreditCreation):
    """
    Creates credits for a given owner.
    Args:
        db (Session): database session.
        credit (schemas.CreditCreation): Credit creation data.
    Returns:
        models.Credit: Created credit.
    Raises:
        UserNotFound: If user with the provided ID does not exists.
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


def create_operation(db: Session, operation: schemas.CreateOperation):
    """
    Create a new operation record in the database.
    Args:
        db (Session): database session.
        operation (schemas.CreateOperation): Operation creation data.
    Returns:
        models.Operation: Created operation.
    """
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

# Functions for updating existing records in the database


def create_max_calls_per_new_user_condition(
    db: Session, condition: schemas.CreateMaxCallsPerSponseeCondition
):
    """
    Create a new condition for maximum calls per sponsee in the database.
    Args:
        db (Session): database session.
        condition: Condition creation data.
    Returns:
        models.Condition: Created conditoin.
    Raises:
        ConditionAlreadyExists: If a condition already exists for the given sponsee address
        and vault ID.
    """
    # Check if a condition already exists for the given sponsee address
    # and vault ID
    existing_condition = (
        db.query(models.Condition)
        .filter(models.Condition.vault_id == condition.vault_id)
        .one_or_none()
    )
    if existing_condition is not None:
        raise ConditionAlreadyExists(
            "A condition with maximum calls per sponsee already exists and the maximum is not reached. Cannot create a new one."
        )

    # Create a new condition for maximum calls per sponsee
    db_condition = models.Condition(
        type=schemas.ConditionType.MAX_CALLS_PER_SPONSEE,
        sponsee_address=condition.sponsee_address,
        vault_id=condition.vault_id,
        max_calls_for_new_user=condition.max,
        current_calls_for_new_user=0,

    )
    db.add(db_condition)
    db.commit()
    db.refresh(db_condition)
    return db_condition


def create_max_calls_per_entrypoint_condition(
    db: Session, condition: schemas.CreateMaxCallsPerEntrypointCondition
):
    """
    Create a new condition for maximum calls per entrypoint in the database.
    Agrs:
        db (Session): database session.
        condition: Condition creation data.
    Returns:
        schemas.MaxCallsPerEntrypointCondition: Created condition.
    Raises:
        ConditionAlreadyExists: If a condition already exists for the given entrypoint,
        contract, and vault.
    """
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
        contract_id=db_condition.contract_id,  # type: ignore
        entrypoint_id=db_condition.entrypoint_id,  # type: ignore
        vault_id=db_condition.vault_id,  # type: ignore
        max=db_condition.max,
        current=db_condition.current,
        type=db_condition.type,  # type: ignore
        created_at=db_condition.created_at,  # type: ignore
        id=db_condition.id,  # type: ignore
    )


def update_entrypoints(db: Session, entrypoints: list[schemas.EntrypointUpdate]):
    """
    Update the 'is_enabled' attribute for a list of entrypoints.
    Args:
        db (Session): database session.
        entrypoints: List of entrypoints to update.
    Returns:
        List[models.Entrypoint]: List of updated entrypoints.
    """
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


def update_user_withdraw_counter(db: Session, user_id: str, withdraw_counter: int):
    """
    Update the withdraw counter for a user.
    Args:
        db (Session): database session.
        user_id (str): ID of the user to update.
        withdraw_counter (int): New withdraw counter value.
    Returns:
        int: Updated withdraw counter value.
    Raises:
        UserNotFound: If the user with the provided ID does not exists.
    """
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


def update_credits(db: Session, credit_update: schemas.CreditUpdate):
    """
    Update the amount of credits for a user.
    Args:
        db (Session): database session.
        credit_update: Database for updating credits.
    Return:
        models.Credit: Updated credit models.
    Raises:
     ContractNotFound: If the credit with the provided ID does not exists.
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
    """
    Update the amount of credits associated with a contract address.
    Args:
        db (Session): database session.
        amount (int): Amount to update the credits by.
        address (str): Address of the contract.
    Returns:
        models.Credit: Updated credit model.
    Raises:
        ContractNotFound: If the contract with the provided address does not exists.
        CreditNotFound: If the associated credit for the contract is not found.
    """
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


def update_amount_operation(db: Session, hash: str, amount: int):
    """
    Update the amount of a specific operation identified by hash.
    Args:
        db (Session): database session.
        hash (str): Hash identifier of the operation to update.
        amount (int): New amount for the operation.
    """
    db.query(models.Operation).filter(models.Operation.hash == hash).update(
        {"cost": amount}
    )
    db.commit()


def update_max_calls_per_month_condition(db: Session, max_calls: int, contract_id):
    """
    Update the maximum calls per month for a specific contract.
    Args:
        db (Session): database session.
        max_calls (int): New maximum calls per month value.
        contract_id: ID of the contract to update.
    Returns:
        models.Contract: Updated contract model.
    """
    db_contract = get_contract(db, contract_id)
    db.query(models.Contract).filter(models.Contract.id == contract_id).update(
        {"max_calls_per_month": max_calls}
    )
    db.commit()
    # db_contract.refresh()
    return db_contract


def update_condition(db: Session, condition: models.Condition):
    """
    Update the current count for a condition.
    Args:
        db (Session): database session.
        condition (models.Condition): Condition to update.
    """
    db.query(models.Condition).filter(models.Condition.id == condition.id).update(
        {"current": condition.current + 1}
    )


def check_calls_per_month(db, contract_id):
    """
    Check if the number of operation for a contract in the current month exceeds the limit.
    Args:
        db: database session.
        contract_id: ID of the contract
    Returns:
        bool: True if within the limit, False otherwise.
    """
    max_calls = get_max_calls_per_month_by_contract_address(db, contract_id)
    # If max_calls is -1 means condition is disabled (NO LIMIT)
    if max_calls == -1:  # type: ignore
        return True
    nb_operations_already_made = get_operations_by_contracts_per_month(
        db, contract_id)
    return max_calls >= len(nb_operations_already_made)


def check_max_calls_per_new_user(db: Session, vault_id: UUID4):
    """
    Check if there is a condition for limiting calls per new user.
    Args:
        db (Session): database session.
        vault_id (UUID4): ID of the vault.
    Returns:
        models.Condition: Condition for limiting calls per new user, if exists
    """
    return (
        db.query(models.Condition)
        .filter(models.Condition.type == schemas.ConditionType.MAX_CALLS_PER_SPONSEE)
        .filter(models.Condition.vault_id == vault_id)
        .one_or_none()
    )


def check_max_calls_per_entrypoint(
    db: Session, contract_id: UUID4, entrypoint_id: UUID4, vault_id: UUID4
):
    """
    Check if there is a condition for limiting calls per entrypoint.
    Args:
        db (Session): database session.
        contract_id (UUID4): ID of the contract.
        entrypoint_id (UUID4): ID of the entrypoint.
        vault_id (UUID4): ID of the vault.
    Returns:
        models.Condition: Condition for limiting calls per entrypoint, if exists.
    """
    return (
        db.query(models.Condition)
        .filter(models.Condition.type == schemas.ConditionType.MAX_CALLS_PER_ENTRYPOINT)
        .filter(models.Condition.contract_id == contract_id)
        .filter(models.Condition.entrypoint_id == entrypoint_id)
        .filter(models.Condition.vault_id == vault_id)
        .one_or_none()
    )


def check_conditions(db: Session, datas: schemas.CheckConditions):
    """
    Check conditions for limiting calls.
    Args:
        db (Session): database session.
        datas: Data containing contract, entrypoing and vault IDs.
    Returns:
        bool: True if conditions are met, False otherwise.
    """
    print(datas)

    # Check if there is a condition for limiting calls for new users
    new_user_condition = check_max_calls_per_new_user(
        db, datas.vault_id
    )

    entrypoint_condition = check_max_calls_per_entrypoint(
        db, datas.contract_id, datas.entrypoint_id, datas.vault_id
    )

    # No condition registered
    if new_user_condition is None and entrypoint_condition is None:
        return True

    # One of condition is excedeed
    if (
        new_user_condition is not None
        and (new_user_condition.current_calls_for_new_user >= new_user_condition.max_calls_for_new_user)
    ) or (
        entrypoint_condition is not None
        and (entrypoint_condition.current >= entrypoint_condition.max)
    ):
        return False

    # Update conditions
    # TODO - Rewrite with list

    if new_user_condition:
        update_condition(db, new_user_condition)
    if entrypoint_condition:
        update_condition(db, entrypoint_condition)
    return True
