from dotenv import load_dotenv
import os
import subprocess


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