# -- EXCEPTIONS --


import enum


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


# -- UTILITY TYPES --
class ConditionType(enum.Enum):
    MAX_CALLS_PER_ENTRYPOINT = "MAX_CALLS_PER_ENTRYPOINT"
    MAX_CALLS_PER_SPONSEE = "MAX_CALLS_PER_SPONSEE"
