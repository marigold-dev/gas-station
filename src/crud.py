from sqlalchemy.orm import Session
from . import models, schemas


def get_user(db: Session, address: str):
  return db.query(models.User).filter(models.User.address == address).first()

def create_user(db: Session, user: schemas.UserCreation):
  db_user = models.User(**user.model_dump())
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
    return contract.entrypoints if contract else []

def get_entrypoint(db: Session, contract_address: str, name: str):
    entrypoints = get_entrypoints(db, contract_address)
    entrypoint = list(filter(lambda e: e.name == name, entrypoints))
    if len(entrypoint) == 0:
        return None
    return entrypoint[0]

def create_contract(db: Session, contract: schemas.ContractCreation):
    c = {k:v for k,v in contract.model_dump().items() if k not in ['entrypoints']}
    db_contract = models.Contract(**c)
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    db_entrypoints =list(map(lambda e: models.Entrypoint(**e.model_dump(), contract_id=db_contract.id), contract.entrypoints))
    db.add_all(db_entrypoints)
    db.commit()
    return db_contract

def update_credits(db: Session, user_update: schemas.UserUpdateCredit):
    db.query(models.User).filter(models.User.address == user_update.address).update({'credits': user_update.credits})
    db.commit()
    return db.query(models.User).filter(models.User.address == user_update.address).first()



# ---- WIP
# def update_credit(contract_address, amount):
#     db = connect()
#     cur = db.cursor()
#     req = f"""UPDATE credits
#         SET credit_amount = credit_amount + {amount}
#         FROM contracts c
#         WHERE credit_id = c.contract_credit
#         AND c.contract_address = '{contract_address}'"""
#     cur.execute(req)
#     cur.close()
#     db.commit()