# Gas station API

Requires Python 3.11.

## Installation
- create an environment (e.g., `python -m venv env`) and activate it (`source env/bin/activate`)
- install dependencies: `pip install -r requirements.txt`
- initialize a PostgreSQL database (named e.g. "gas_station") and complete `sql/database.ini` accordingly
- write a `.env`, e.g.:

```
TEZOS_RPC=https://ghostnet.tezos.marigold.dev
SECRET_KEY_CMD='echo [a secret key]'
```

You can provide a `SECRET_KEY` as the result of a command, or directly in the `.env` file using
`SECRET_KEY` instead.

- run the API: `uvicorn src.main:app --reload`

If it doesn't work out the box, please open an issue.

## Restrictions

- the SENDER of the transactions is always going to be the API, i.e., the account used in the .env
  file;
- the contracts must expect additional information in their entrypoints, such as the sender
  ("actual" owner of the assets).

Good luck!

TEST