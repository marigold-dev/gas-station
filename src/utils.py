# -- EXCEPTIONS --
class UserNotFound(Exception):
    pass


class ContractNotFound(Exception):
    pass


class EntrypointNotFound(Exception):
    pass


class CreditNotFound(Exception):
    pass


class ConfigurationError(Exception):
    pass


class OperationNotFound(Exception):
    pass


class ContractAlreadyRegistered(Exception):
    pass
