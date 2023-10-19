import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import database as db, routes, models, tezos

models.Base.metadata.create_all(bind=db.engine)

app = FastAPI()

app.include_router(routes.router)

# TODO:https://github.com/marigold-dev/gas-station/issues/3
# origins = [
#     "http://localhost:5173",
#     "http://localhost:3000"
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

loop = asyncio.get_event_loop()

try:
    asyncio.ensure_future(tezos.tezos_manager.main_loop())
except KeyboardInterrupt:
    pass
