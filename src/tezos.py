from collections import OrderedDict
import asyncio
from typing import Union

from src import database
# from .pytezos import ptz, pytezos
from . import crud, schemas
from pytezos.rpc.errors import MichelsonError
from pytezos.michelson.types import MichelsonType
import pytezos

from . import config

# Config stuff for pytezos
assert config.SECRET_KEY is not None and len(config.SECRET_KEY) > 0, \
  "Could not read secret key"

admin_key = pytezos.pytezos.key.from_encoded_key(
    config.SECRET_KEY
)
ptz = pytezos.pytezos.using(config.TEZOS_RPC, admin_key)
print(f"INFO: API address is {ptz.key.public_key_hash()}")
constants = ptz.shell.block.context.constants()


class OperationNotFound(Exception):
    pass


async def find_transaction(tx_hash):
    block_time = int(constants["minimal_block_delay"])
    nb_try = 0
    while nb_try < 4:
        try:
            op_result = ptz.shell.blocks[-10:].find_operation(tx_hash)
            break
        except Exception:
            nb_try += 1
            await asyncio.sleep(block_time)
    else:
        raise OperationNotFound(tx_hash)

    return op_result


def find_fees(global_tx, payer_key):
    """Find the baker and storage fees in the operation result
    returns the operation indice as well, as the length of the fees
    of one operation in the bulk may vary"""
    op_result = global_tx["contents"]
    fees = [
        (int(z["change"]), x["destination"])
        for x in op_result
        for y in (
            x["metadata"].get(
                "operation_result", {}
            ).get("balance_updates", {}),
            x["metadata"].get("balance_updates", {}),
        )
        for z in y
        if z.get("contract", "") == payer_key
    ]
    return fees


def group_fees(fees: list[tuple[int, str]]):
    """Expects a list of (fee, contract_address) and returns the sum
    of fees by contract."""
    grouped_fees = {}
    for fee, address in fees:
        grouped_fees[address] = grouped_fees.get(address, 0) + fee
    return grouped_fees


def check_credits(db, estimated_fees):
    for address, total_fee in estimated_fees.items():
        credits = crud.get_credits_from_contract_address(db, address)
        if total_fee > credits.amount:
            print(f"Unsufficient credits {credits.amount} for contract" \
                  + f"{address}; total fees are {total_fee}.")
            return False
    return True


async def confirm_deposit(tx_hash, payer, amount: Union[int, str]):
    receiver = ptz.key.public_key_hash()
    op_result = await find_transaction(tx_hash)
    return any(
        op for op in op_result["contents"]
        if op["kind"] == "transaction"
        and op["source"] == payer
        and op["destination"] == receiver
        and int(op["amount"]) == int(amount)
    )


async def confirm_withdraw(tx_hash, db, user_id, withdraw):
    await find_transaction(tx_hash)
    credit_update = schemas.CreditUpdate(id=withdraw.id,
                                         amount=-withdraw.amount,
                                         owner_id=user_id, operation_hash="")
    crud.update_credits(db, credit_update)


def simulate_transaction(operations):
    op = ptz.bulk(
        *[
            ptz.transaction(
                source=ptz.key.public_key_hash(),
                parameters=operation["parameters"],
                destination=operation["destination"],
                amount=0,
            )
            for operation in operations
        ]  # type: ignore
    )
    return op.autofill()


def get_public_key(address):
    assert address.startswith("tz")
    key = ptz.shell.head.context.contracts[address].manager_key()
    return key


def check_signature(pair_data, signature, public_key):
    # Type of a withdraw operation
    pair_type = {
        "prim": 'pair',
        "args": [
            {"prim": 'string'},
            {"prim": "int"},
            {"prim": 'mutez'}
        ]
    }
    public_key = pytezos.Key.from_encoded_key(public_key)
    matcher = MichelsonType.match(pair_type)
    packed_pair = matcher.from_micheline_value(pair_data).pack()
    try:
        # .verify raises an exception when the verification fails
        return public_key.verify(message=packed_pair, signature=signature)
    except ValueError:
        return False


async def withdraw(tezos_manager, to, amount):
    op = ptz.transaction(source=ptz.key.public_key_hash(),
                         destination=to,
                         amount=amount).autofill()
    return await tezos_manager.queue_operation(sender=to, operation=op)


class TezosManager:
    def __init__(self, ptz):
        self.ops_queue = OrderedDict()
        self.results = dict()  # TODO: find inspiration
        self.ptz = ptz
        self.block_time = int(constants["minimal_block_delay"])

    # Receive an operation from sender and add it to the waiting queue;
    # blocks until there is a result in self.results
    async def queue_operation(self, sender, operation):
        self.results[sender] = "waiting"
        self.ops_queue[sender] = operation
        while self.results[sender] == "waiting":
            # TODO wait the right amount of time
            # FIXME add max waiting time
            await asyncio.sleep(1)

        if self.results[sender] == "waiting":
            raise Exception()

        return {
            "result": "ok",
            "transaction_hash": self.results[sender]["transaction"].hash(),
        }

    async def update_fees(self, posted_tx):
        op_result = await find_transaction(posted_tx.hash())
        fees = find_fees(op_result, ptz.key.public_key_hash())
        fees = group_fees(fees)
        try:
            db = database.SessionLocal()
            for contract, fee in fees.items():
                # If this is a transfer to a tz1, then it's a withdraw
                # and the fees do not matter.
                # Feels a bit hackish though.
                if contract.startswith("tz"):
                    continue
                crud.update_credits_from_contract_address(db,
                                                          amount=fee,
                                                          address=contract)
        finally:
            db.close()

    async def main_loop(self):
        while True:
            try:
                await asyncio.sleep(self.block_time)
                # TODO make sure we are in a new block, otherwise continue
                # TODO catch errors

                n_ops = len(self.ops_queue)
                print(f"found {n_ops} operations to send")
                acceptable_operations = OrderedDict()
                for sender in self.ops_queue:
                    op = self.ops_queue[sender]
                    acceptable_operations[sender] = op
                    try:
                        ptz.bulk(*acceptable_operations.values()).autofill()
                    except MichelsonError:
                        # The last operation conflicts with some of the others;
                        # we refuse it
                        acceptable_operations.pop(sender)
                        self.results[sender] = "failing"

                n_ops = len(acceptable_operations)
                print(f"found {n_ops} valid operations to send")
                if n_ops > 0:
                    # Post all the correct operations together and get the
                    # result from the RPC to know what the real fees were
                    posted_tx = ptz.bulk(*acceptable_operations.values()).send()
                    for i, k in enumerate(acceptable_operations):
                        assert self.results[k] != "failing"
                        self.results[k] = {"transaction": posted_tx}
                    asyncio.create_task(self.update_fees(posted_tx))
                self.ops_queue = dict()
                print("Tezos loop executed")
            except Exception:
                #FIXME: Should we raise an Exception here ?
                pass



tezos_manager = TezosManager(ptz)
