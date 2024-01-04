from src import crud

# -- EXCEPTIONS --


class UserNotFound(Exception):
    pass


class ContractNotFound(Exception):
    pass


class EntrypointNotFound(Exception):
    pass


class EntrypointDisabled(Exception):
    pass


class CreditNotFound(Exception):
    pass


class ConfigurationError(Exception):
    pass


class OperationNotFound(Exception):
    pass


class ContractAlreadyRegistered(Exception):
    pass


class NotEnoughFunds(Exception):
    pass


class TooManyCallsForThisMonth(Exception):
    pass


def check_calls_per_month(db, contract_id):
    max_calls = crud.get_max_calls_per_month_by_contract_address(db, contract_id)
    # If max_calls is -1 means condition is disabled (NO LIMIT)
    if max_calls == -1:  # type: ignore
        return True
    nb_operations_already_made = crud.get_operations_by_contracts_per_month(
        db, contract_id
    )
    return max_calls >= len(nb_operations_already_made)
