from sqlalchemy.orm import Session
from . import models, schemas

def find(command):
    db = connect()
    cur = db.cursor()
    cur.execute(command)
    res = cur.fetchall()
    cur.close()
    db.close()
    return res


# def find_contract(contract_address):
#     return find(f"SELECT contract_id \
#                 FROM contracts WHERE contract_address='{contract_address}'")


def find_entrypoint(contract_id, entrypoint):
    return find(f"SELECT entrypoint_id \
                FROM entrypoints WHERE contract_id='{contract_id}'")


def update_credit(contract_address, amount):
    db = connect()
    cur = db.cursor()
    req = f"""UPDATE credits
        SET credit_amount = credit_amount + {amount}
        FROM contracts c
        WHERE credit_id = c.contract_credit
        AND c.contract_address = '{contract_address}'"""
    cur.execute(req)
    cur.close()
    db.commit()

# def find_contracts_by_user(user_address):
#     return find(f"SELECT * FROM contracts JOIN users ON contracts.owner_id = users.user_id WHERE users.user_address = '{user_address}'")

# def find_user_by_address(user_address):
#     return find(f"SELECT users.user_id \
#                 FROM users WHERE users.user_address='{user_address}'")

# def add_user(user_address, user_name):
#     db = connect()
#     cur = db.cursor()
#     req = f"""
#         INSERT INTO users ("user_name", "user_address") VALUES ('{user_name}', '{user_address}') RETURNING *;
#     """
#     cur.execute(req)
#     new_user = cur.fetchone()
#     cur.close()
#     db.commit()
#     return new_user

def add_contract(name, address, entrypoints, owner):
    db = connect()
    cur = db.cursor()
    req = f"""

    """
    return


# --------- WIP --------- #

def get_user(db: Session, address: str):
  return db.query(models.User).filter(models.User.address == address).first()

def create_user(db: Session, user: schemas.UserCreation):
  db_user = models.User(**user.dict())
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def get_contracts_by_user(db: Session, user_address: str):
    user = get_user(db, user_address)
    if not user:
        return None
    return user.contracts


def get_contract(db: Session, address: str):
    return db.query(models.Contract).filter(models.Contract.address == address).first()


def get_entrypoints(db: Session, contract_address: str):
    contract = get_contract(db, contract_address)
    return contract.entrypoints

def get_entrypoint(db: Session, contract_address: str, name: str):
    entrypoints = get_entrypoints(db, contract_address)
    entrypoint = list(filter(lambda e: e.name == name, entrypoints))
    if len(entrypoint) == 0:
        return None
    return entrypoint[0]