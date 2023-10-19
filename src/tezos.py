from collections import OrderedDict
import asyncio

from src import database
# from .pytezos import ptz, pytezos
from . import crud
from .schemas import CreditUpdate
from pytezos.rpc.errors import MichelsonError
from pytezos import PyTezosClient
import pytezos
from sqlalchemy.orm import Session

from . import config

# Config stuff for pytezos
assert config.SECRET_KEY is not None and len(config.SECRET_KEY) > 0, \
  "Could not read secret key"

admin_key = pytezos.pytezos.key.from_encoded_key(
    config.SECRET_KEY
)
ptz = pytezos.pytezos.using(config.TEZOS_RPC, admin_key)


async def find_transaction(tx_hash, block_time):
    nb_try = 0
    while nb_try < 4:
        try:
            op_result = ptz.shell.blocks[-10:].find_operation(tx_hash)
            break
        except Exception:
            nb_try += 1
            await asyncio.sleep(block_time)
    else:
        raise Exception(f"Couldn't find operation {tx_hash}")

    return op_result


def find_fees(global_tx, payer_key):
    """Find the baker and storage fees in the operation result
    returns the operation indice as well, as the length of the fees
    of one operation in the bulk may vary"""
    op_result = global_tx["contents"]
    fees = [
        (z, x["destination"])
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


def confirm_amount(tx_hash, payer, amount: int | str):
    receiver = ptz.key.public_key_hash()
    op_result = find_transaction(tx_hash)
    return any(
        op for op in op_result["contents"]
        if op["kind"] == "transaction"
        and op["source"] == payer
        and op["destination"] == receiver
        and int(op["amount"]) == amount
    )


class TezosManager:
    def __init__(self, ptz):
        self.ops_queue = OrderedDict()
        self.results = dict()  # TODO: find inspiration
        self.ptz = ptz
        constants = self.ptz.shell.block.context.constants()
        self.block_time = int(constants["minimal_block_delay"])

    # Receive an operation from sender and add it to the waiting queue;
    # blocks until there is a result in self.results
    async def queue_operation(self, sender, operation):
        self.results[sender] = "waiting"
        self.ops_queue[sender] = operation
        while self.results[sender] == "waiting":
            # TODO wait the right amount of time
            await asyncio.sleep(1)

        if self.results[sender] == "waiting":
            raise Exception()

        return {
            "result": "ok",
            "transaction_hash": self.results[sender]["transaction"].hash(),
        }

    async def update_fees(self, posted_tx):
        db = database.SessionLocal()
        op_result = await find_transaction(posted_tx.hash())
        fees = find_fees(op_result, ptz.key.public_key_hash())
        # TODO group requests
        try:
            for fee, contract in fees:
                crud.update_credits(db,
                                    amount=int(fee["change"]),
                                    address=contract)
                crud.update_amount_operation(db,
                                             op_result["hash"],
                                             int(fee["change"]))
        finally:
            db.close()

    async def main_loop(self):
        while True:
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


tezos_manager = TezosManager(ptz)
