from typing import Any
from collections import OrderedDict
import asyncio

import pytezos
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# FIXME
TEZOS_RPC = "https://ghostnet.smartpy.io"
app = FastAPI()

# FIXME
admin_key = pytezos.Key.from_encoded_key(
    "edsk3QoqBuvdamxouPhin7swCvkQNgq4jP5KZPbwWNnwdZpSpJiEbq"
)
ptz = pytezos.pytezos.using(TEZOS_RPC, admin_key)

# FIXME
allowed_entrypoints = {
    "KT1GPCSN88jU1EnmNvnnngnneowwAMrefbMx": ["stake", "unstake"],
    "KT1BbUsGvsCdDgRoidDGrY7wyWu7uutBrphA": ["mint_token", "permit"]
}

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


class TezosManager:
    def __init__(self, ptz):
        self.ops_queue = OrderedDict()
        self.results = dict()  # TODO: find inspiration
        self.ptz = ptz
        constants = self.ptz.shell.block.context.constants()
        self.block_time = int(constants["minimal_block_delay"])

    # Receive an operation from sender and add it to the waiting queue;
    # blocks until there is a result in self.results
    # TODO: accept and queue several operations for a given sender
    async def queue_operation(self, sender, operation):
        self.results[sender] = "waiting"
        self.ops_queue[sender] = operation
        while self.results[sender] == "waiting":
            # TODO wait the right amount of time
            await asyncio.sleep(self.block_time)
        return self.results[sender]

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
    contract_address: str
    parameters: dict[str, Any]


@app.post("/operation")
async def post_operation(call_data: CallData):
    contract_address = call_data.contract_address
    if contract_address not in allowed_entrypoints:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Target {call_data.contract_address} is not allowed"
        )

    entrypoint = call_data.parameters["entrypoint"]
    if entrypoint not in allowed_entrypoints[contract_address]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Entrypoint {entrypoint} is not allowed"
        )
    op = ptz.transaction(
        source=ptz.key.public_key_hash(),
        parameters=call_data.parameters,
        destination=call_data.contract_address,
        amount=0
    )
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
finally:
    print("Closing Loop")
