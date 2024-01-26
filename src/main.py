import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import database as db, routes, models, tezos

# Database setup
# Create the database tables
models.Base.metadata.create_all(bind=db.engine)

# FastAPI application setup
app = FastAPI()
app.include_router(routes.router)

# TODO:https://github.com/marigold-dev/gas-station/issues/3
# origins = [
#     "http://localhost:5173",
#     "http://localhost:3000"
# ]

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # allow any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Asynchronous loop setup
loop = asyncio.get_event_loop()

# try-except block catches a KeyboardInterrupt exception
# to handle a graceful shutdown if the loop is interrupted
try:
    # try to start an asynchronous task, suggests that
    # there is an asynchronous loop managed by tezos_manager.main_loop function
    asyncio.ensure_future(tezos.tezos_manager.main_loop())
except KeyboardInterrupt:
    pass
