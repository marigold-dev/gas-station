# -- EXCEPTIONS --


import enum


class SponsorNotFound(Exception):
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


class ConditionAlreadyExists(Exception):
    pass


class ConditionExceed(Exception):
    pass
