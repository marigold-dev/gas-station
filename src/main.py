from typing import Any
from collections import OrderedDict
import asyncio
import os
import subprocess
from dotenv import load_dotenv

import pytezos
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import database as db

load_dotenv()
TEZOS_RPC = os.getenv('TEZOS_RPC')
SECRET_KEY_CMD = os.getenv('SECRET_KEY_CMD')
if SECRET_KEY_CMD is not None:
    command = SECRET_KEY_CMD.split()
    sub = subprocess.run(command, stdout=subprocess.PIPE)
    SECRET_KEY = sub.stdout.decode('utf-8').strip()
else:
    SECRET_KEY = os.getenv('SECRET_KEY')

assert TEZOS_RPC is not None, "Please specify a TEZOS_RPC"
assert SECRET_KEY is not None and len(SECRET_KEY) > 0, \
    "Could not read secret key"

app = FastAPI()

admin_key = pytezos.Key.from_encoded_key(
    SECRET_KEY
)
ptz = pytezos.pytezos.using(TEZOS_RPC, admin_key)

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def find_fees(global_tx, payer_key):
    """Find the baker and storage fees in the operation result
    returns the operation indice as well, as the length of the fees
    of one operation in the bulk may vary"""
    op_result = global_tx["contents"]
    print(op_result)
    fees = [
        (z, x["destination"])
          for x in op_result
          for y in (x["metadata"].get("operation_result", {}).get("balance_updates", {}),
                    x["metadata"].get("balance_updates", {}))
          for z in y
          if z.get("contract", "") == payer_key
    ]
    print(fees)
    return fees


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
            await asyncio.sleep(self.block_time)
        return self.results[sender]
    async def update_fees(self, posted_tx):
        nb_try = 0
        while nb_try < 4:
            try:
                op_result = ptz.shell.blocks[-10:].find_operation(posted_tx.hash())
                break
            except Exception as _e:
                nb_try += 1
                await asyncio.sleep(self.block_time)
        else:
            raise Exception(f"Couldn't find operation {posted_tx.hash()}")
        fees = find_fees(op_result, ptz.key.public_key_hash())
        # TODO group requests
        for (fee, contract) in fees:
            db.update_credit(contract, int(fee["change"]))

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
                except pytezos.rpc.errors.MichelsonError:
                    # The last operation conflicts with some of the others;
                    # we refuse it
                    acceptable_operations.pop(sender)
                    self.results[sender] = "failing"

            n_ops = len(acceptable_operations)
            print(f"found {n_ops} valid operations to send")
            if n_ops > 0:
                posted_bulk = ptz.bulk(*acceptable_operations.values()).send()
                for k in acceptable_operations:
                    assert self.results[k] != "failing"
                    self.results[k] = posted_bulk.hash()
            self.ops_queue = dict()
            print("Tezos loop executed")


tezos_manager = TezosManager(ptz)


# TODO: right now the sender isn't checked, as we use permits anyway
class CallData(BaseModel):
    sender: str
    operations: list[dict[str, Any]]


@app.post("/operation")
async def post_operation(call_data: CallData):
    if len(call_data.operations) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Empty operations list"
        )

    # TODO: check that amount=0?
    for operation in call_data.operations:
        contract_address = operation["destination"]

        # Transfers to implicit accounts are always refused
        if not contract_address.startswith("KT"):
            raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Target {contract_address} is not allowed"
                )
        contracts = db.find_contract(contract_address)
        if len(contracts) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Target {contract_address} is not allowed"
            )

        contract_id = contracts[0][0]  # First row
        entrypoint = operation["parameters"]["entrypoint"]
        entrypoints = db.find_entrypoint(
            contract_id,
            entrypoint
        )
        if len(entrypoints) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Entrypoint {entrypoint} is not allowed"
            )
    op = ptz.bulk(*[
        ptz.transaction(
            source=ptz.key.public_key_hash(),
            parameters=operation["parameters"],
            destination=operation["destination"],
            amount=0
        )
        for operation in call_data.operations
    ])
    # TODO: log the result
    try:
        # Simulate the operation alone without sending it
        op.autofill()
        result = await tezos_manager.queue_operation(call_data.sender, op)
    except pytezos.rpc.errors.MichelsonError as e:
        print("Received failing operation, discarding")
        print(e)
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation is invalid"
            )
    if result == "failing":
        raise HTTPException(
            # FIXME? Is this the best one?
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation is invalid"
        )

    return {"hash": result}

loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(tezos_manager.main_loop())
except KeyboardInterrupt:
    pass
