from fastapi import APIRouter, HTTPException, status, Depends
import asyncio

from sqlalchemy.orm import Session
from . import tezos, crud, schemas, database
from pytezos.rpc.errors import MichelsonError
from pytezos.crypto.encoding import is_address
from .utils import (
    ConditionAlreadyExists,
    ConditionExceed,
    ContractAlreadyRegistered,
    ContractNotFound,
    CreditNotFound,
    EntrypointDisabled,
    EntrypointNotFound,
    TooManyCallsForThisMonth,
    NotEnoughFunds,
    SponsorNotFound,
    OperationNotFound,
)
from .config import logging
from .schemas import ConditionType


router = APIRouter()

#! API Routes


# Healthcheck
@router.get("/")
async def root():
    return {"status": "healthy", "tezos_address": tezos.public_address}


# POST endpoints
@router.post("/sponsors", response_model=schemas.Sponsor)
async def create_sponsor(
    sponsor: schemas.SponsorCreation, db: Session = Depends(database.get_db)
):
    sponsor = crud.create_sponsor(db, sponsor)
    crud.create_credits(db, schemas.CreditCreation(owner_id=sponsor.id))
    return sponsor


@router.post("/contracts", response_model=schemas.Contract)
async def create_contract(
    contract: schemas.ContractCreation, db: Session = Depends(database.get_db)
):
    try:
        return crud.create_contract(db, contract)
    except ContractAlreadyRegistered:
        logging.warn(f"Contract {contract.address} is already registered")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Contract {contract.address} is already registered.",
        )


# PUT endpoints
@router.put("/entrypoints", response_model=list[schemas.Entrypoint])
async def update_entrypoints(
    entrypoints: list[schemas.EntrypointUpdate], db: Session = Depends(database.get_db)
):
    return crud.update_entrypoints(db, entrypoints)


@router.put("/deposit", response_model=schemas.Credit)
async def update_credits(
    credits: schemas.CreditUpdate, db: Session = Depends(database.get_db)
):
    try:
        payer_address = crud.get_credits(db, credits.id).owner.tezos_address
        op_hash = credits.operation_hash
        amount = credits.amount
        is_confirmed = await tezos.confirm_deposit(op_hash, payer_address, amount)
        if not is_confirmed:
            logging.warning(f"Could not find confirmation for {amount} with {op_hash}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not find confirmation for {amount} with {op_hash}",
            )
        return crud.update_credits(db, credits)
    except ContractNotFound:
        logging.warning(f"Contrat not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contrat not found.",
        )
    except CreditNotFound:
        logging.warning(f"Credit not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit not found.",
        )
    except OperationNotFound:
        logging.warning(f"Could not find the operation.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find the operation.",
        )


@router.put("/withdraw")
async def withdraw_credits(
    withdraw: schemas.CreditWithdraw, db: Session = Depends(database.get_db)
):
    try:
        credits = crud.get_credits(db, withdraw.id)
    except CreditNotFound:
        logging.warning(f"Credit not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit not found.",
        )
    if credits.amount < withdraw.amount:
        logging.warning(f"Not enough funds to withdraw credit ID {withdraw.id}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough funds to withdraw.",
        )

    expected_counter = credits.owner.withdraw_counter or 0
    if expected_counter != withdraw.withdraw_counter:
        logging.warning(f"Withdraw counter provided is not the expected counter.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad withdraw counter."
        )

    owner_address = credits.owner.tezos_address
    sponsor = crud.get_sponsor_by_address(db, owner_address)
    public_key = tezos.get_public_key(owner_address)
    is_valid = tezos.check_signature(
        withdraw.to_micheline_pair(), withdraw.micheline_signature, public_key
    )
    if not is_valid:
        logging.warning(f"Invalid signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature."
        )
    # We increment the counter even if the withdraw fails to prevent
    # the counter from being used again immediately.
    counter = crud.update_sponsor_withdraw_counter(
        db, str(sponsor.id), withdraw.withdraw_counter + 1
    )
    result = await tezos.withdraw(tezos.tezos_manager, owner_address, withdraw.amount)
    if result["result"] == "ok":
        logging.debug(f"Start to confirm withdraw for {result['transaction_hash']}")
        # Starts a independent loop to check that the operation
        # has been confirmed
        asyncio.create_task(
            tezos.confirm_withdraw(
                result["transaction_hash"], db, str(sponsor.id), withdraw
            )
        )

    return {**result, "counter": counter}


# Sponsors and credits getters
@router.get("/sponsors/{address_or_id}", response_model=schemas.Sponsor)
async def get_sponsor(address_or_id: str, db: Session = Depends(database.get_db)):
    try:
        if is_address(address_or_id) and address_or_id.startswith("tz"):
            return crud.get_sponsor_by_address(db, address_or_id)
        else:
            return crud.get_sponsor(db, address_or_id)
    except SponsorNotFound:
        logging.warning(f"Sponsor {address_or_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsor not found.",
        )


@router.get("/credits/{sponsor_address_or_id}", response_model=list[schemas.Credit])
async def credits_for_sponsor(
    sponsor_address_or_id: str, db: Session = Depends(database.get_db)
):
    try:
        if is_address(sponsor_address_or_id) and sponsor_address_or_id.startswith("tz"):
            return crud.get_sponsor_by_address(db, sponsor_address_or_id).credits
        else:
            return crud.get_sponsor(db, sponsor_address_or_id).credits
    except SponsorNotFound:
        logging.warning(f"Sponsor {sponsor_address_or_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsor not found.",
        )


# Contracts
@router.get("/contracts/sponsor/{sponsor_address}", response_model=list[schemas.Contract])
async def get_sponsor_contracts(sponsor_address: str, db: Session = Depends(database.get_db)):
    try:
        return crud.get_contracts_by_sponsor(db, sponsor_address)
    except SponsorNotFound:
        logging.warning(f"Sponsor {sponsor_address} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Sponsor not found."
        )


@router.get("/contracts/credit/{credit_id}", response_model=list[schemas.Contract])
async def get_credit(credit_id: str, db: Session = Depends(database.get_db)):
    try:
        return crud.get_contracts_by_credit(db, credit_id)
    except CreditNotFound:
        logging.warning(f"Credit {credit_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Credit not found."
        )


@router.get("/contracts/{address_or_id}", response_model=schemas.Contract)
async def get_contract(address_or_id: str, db: Session = Depends(database.get_db)):
    if is_address(address_or_id) and address_or_id.startswith("KT"):
        contract = crud.get_contract_by_address(db, address_or_id)
    else:
        contract = crud.get_contract(db, address_or_id)
    if not contract:
        logging.warning(f"Contract {address_or_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract not found."
        )
    return contract


# Entrypoints
@router.get(
    "/entrypoints/{contract_address_or_id}", response_model=list[schemas.Entrypoint]
)
async def get_entrypoints(
    contract_address_or_id: str, db: Session = Depends(database.get_db)
):
    try:
        if contract_address_or_id.startswith("KT"):
            assert is_address(contract_address_or_id)
        return crud.get_entrypoints(db, contract_address_or_id)
    except ContractNotFound:
        logging.warning(f"Contract {contract_address_or_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract not found."
        )
    except AssertionError:
        logging.warning(f"Invalid address {contract_address_or_id} provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid address."
        )


@router.get(
    "/entrypoints/{contract_address_or_id}/{name}", response_model=schemas.Entrypoint
)
async def get_entrypoint(
    contract_address_or_id: str, name: str, db: Session = Depends(database.get_db)
):
    try:
        return crud.get_entrypoint(db, contract_address_or_id, name)
    except EntrypointNotFound:
        logging.warning(f"Entrypoint {contract_address_or_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entrypoint not found."
        )


# Operations
@router.post("/operation")
async def post_operation(
    call_data: schemas.UnsignedCall, db: Session = Depends(database.get_db)
):
    if len(call_data.operations) == 0:
        logging.warning(f"Operations list is empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Empty operations list",
        )
    # TODO: check that amount=0?
    for operation in call_data.operations:
        contract_address = str(operation["destination"])

        # Transfers to implicit accounts are always refused
        if not contract_address.startswith("KT"):
            logging.warning(f"Target {contract_address} is not allowed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target {contract_address} is not allowed",
            )
        try:
            contract = crud.get_contract_by_address(db, contract_address)
        except ContractNotFound:
            logging.warning(f"{contract_address} is not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{contract_address} is not found",
            )

        entrypoint_name = operation["parameters"]["entrypoint"]

        try:
            entrypoint = crud.get_entrypoint(db, str(contract.address), entrypoint_name)
            if not entrypoint.is_enabled:
                raise EntrypointDisabled()

            if not crud.check_conditions(
                db,
                schemas.CheckConditions(
                    sponsee_address=call_data.sender_address,
                    contract_id=contract.id,
                    entrypoint_id=entrypoint.id,
                    vault_id=contract.credit_id,
                ),
            ):
                raise ConditionExceed()
        except EntrypointNotFound:
            logging.warning(f"Entrypoint {entrypoint_name} is not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Entrypoint {entrypoint_name} is not found",
            )
        except EntrypointDisabled:
            logging.warning(f"Entrypoint {entrypoint_name} is disabled.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Entrypoint {entrypoint_name} is disabled.",
            )
        except ConditionExceed:
            logging.warning(f"A condition exceed the maximum defined.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A condition exceed the maximum defined.",
            )

    try:
        # Simulate the operation alone without sending it
        # TODO: log the result
        op = tezos.simulate_transaction(call_data.operations)

        logging.debug(f"Result of operation simulation : {op}")

        op_estimated_fees = [(int(x["fee"]), x["destination"]) for x in op.contents]
        estimated_fees = tezos.group_fees(op_estimated_fees)

        logging.debug(f"Estimated fees: {estimated_fees}")

        if not tezos.check_credits(db, estimated_fees):
            logging.warning(f"Not enough funds to pay estimated fees.")
            raise NotEnoughFunds(
                f"Estimated fees : {estimated_fees[str(contract.address)]} mutez"
            )
        if not crud.check_calls_per_month(db, contract.id):  # type: ignore
            logging.warning(f"Too many calls made for this contract this month.")
            raise TooManyCallsForThisMonth()

        result = await tezos.tezos_manager.queue_operation(call_data.sender_address, op)

        crud.create_operation(
            db,
            schemas.CreateOperation(
                sender_address=call_data.sender_address,
                contract_id=str(contract.id),
                entrypoint_id=str(entrypoint.id),
                hash=result["transaction_hash"],
                status=result["result"],  # type: ignore
            ),
        )
    except MichelsonError as e:
        print("Received failing operation, discarding")
        logging.error(f"Invalid operation {e}")
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Operation is invalid",
        )
    except NotEnoughFunds as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Not enough funds. {e}"
        )
    except TooManyCallsForThisMonth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Too many calls made for this contract this month.",
        )
    except Exception as e:
        logging.error(f"Unknown error on /operation : {e}")
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown exception raised.",
        )
    return result


@router.post("/signed_operation")
async def signed_operation(
    call_data: schemas.SignedCall, db: Session = Depends(database.get_db)
):
    # In order to check the signed Micheline
    # FIXME: this is a serious issue, we should sign the contract address too.
    signed_data = [x["parameters"]["value"] for x in call_data.operations]
    if not tezos.check_signature(
        signed_data, call_data.signature, call_data.sender_key, call_data.micheline_type
    ):
        logging.warning("Invalid signature.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature."
        )
    address = tezos.public_key_hash(call_data.sender_key)
    call_data_unsigned = schemas.UnsignedCall(
        sender_address=address, operations=call_data.operations
    )
    return await post_operation(call_data_unsigned, db)


@router.put(
    "/contract/{contract_id}/condition/max_calls", response_model=schemas.Contract
)
async def update_max_calls(
    contract_id: str,
    body: schemas.UpdateMaxCallsPerMonth,
    db: Session = Depends(database.get_db),
):
    if body.max_calls < -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Max calls cannot be < -1"
        )
    return crud.update_max_calls_per_month_condition(db, body.max_calls, contract_id)


@router.post("/condition")
async def create_condition(
    body: schemas.CreateCondition, db: Session = Depends(database.get_db)
):
    try:
        if (
            body.type == ConditionType.MAX_CALLS_PER_ENTRYPOINT
            and body.contract_id is not None
            and body.entrypoint_id is not None
        ):
            return crud.create_max_calls_per_entrypoint_condition(
                db,
                schemas.CreateMaxCallsPerEntrypointCondition(
                    contract_id=body.contract_id,
                    vault_id=body.vault_id,
                    max=body.max,
                    entrypoint_id=body.entrypoint_id,
                ),
            )
        elif (
            body.type == ConditionType.MAX_CALLS_PER_SPONSEE
            and body.contract_id is not None
        ):
            return crud.create_max_calls_per_sponsee_condition(
                db,
                schemas.CreateMaxCallsPerSponseeCondition(
                    contract_id=body.contract_id,
                    vault_id=body.vault_id,
                    max=body.max,
                ),
            )
        else:
            logging.error("Unknown condition or missing parameters.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown condition or missing parameters.",
            )
    except ConditionAlreadyExists as e:
        logging.warning(e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/condition/{vault_id}")
async def get_conditions_by_vault(
    vault_id: str, db: Session = Depends(database.get_db)
):
    return crud.get_conditions_by_vault(db, vault_id)
