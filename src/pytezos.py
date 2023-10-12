import pytezos
from . import config


assert config.SECRET_KEY is not None and len(config.SECRET_KEY) > 0, \
  "Could not read secret key"

admin_key = pytezos.pytezos.key.from_encoded_key(
    config.SECRET_KEY
)

ptz = pytezos.pytezos.using(config.TEZOS_RPC, admin_key)