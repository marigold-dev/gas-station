import asyncio
from typing import Any
import os
import requests

from fastapi import FastAPI, APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from Crypto.PublicKey import RSA
import jwt

api_url = os.getenv("GAS_STATION_URL")
gs_user_address = "tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb"
router = APIRouter()


class Operation(BaseModel):
    """Data sent when posting an operation. The sender is mandatory."""

    sender_address: str
    operations: list[dict[str, Any]]


# TODO: the signature should include the action decided by the sponsor API
class Receipt(BaseModel):
    """Signature of an operation to be posted on-chain."""
    gas_station_action: str
    signature: str


try:
    skey = "".join(open("./private.pem").readlines())
    pkey = "".join(open("./public.pem").readlines())
except FileNotFoundError:
    mykey = RSA.generate(1024)
    skey = mykey.export_key()
    pkey = mykey.public_key().export_key()
    with open("./private.pem", "w") as f:
        f.write(skey)
    with open("./public.pem", "w") as f:
        f.write(pkey)


# We will assume this API runs in only one thread, and ignore race conditions
# for this example.
# Shared database of senders, to limit the number of sponsored operations
# per user. This could be implemented as a condition directly in the gas
# station as well.
seen_senders = dict()


def validate(sender):
    seen = seen_senders.get(sender, 0)
    print("SEEN", seen, "TIMES")
    if seen > 1:
        return False
    else:
        seen_senders[sender] = seen + 1
        return True


@router.post("/operation", response_model=Receipt)
async def sign_operation(request: Request):
    raw_operation = await request.json()
    try:
        operation = Operation.parse_obj(raw_operation)
    except:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse operation",
        )

    if validate(operation.sender_address):
        signature = jwt.encode(
            raw_operation, key=skey, algorithm="RS256"
        )
        return Receipt(
            gas_station_action="post_operation",
            signature=signature
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                {
                    "detail": "Invalid call",
                    "body": "FIXME",
                    "custom msg": ""
                }
            )
        )

# TODO
# - implement "operation_posted"

# Register to the API
r = requests.get(f"{api_url}/sponsors/{gs_user_address}")
gs_user = r.json()
requests.put(
    f"{api_url}/sponsor_api",
    json = {
        "sponsor_id": gs_user["id"],
        "api_url": "http://localhost:8005",  # This API
        "public_key": pkey
    }
)

app = FastAPI()
app.include_router(router)

loop = asyncio.get_event_loop()
