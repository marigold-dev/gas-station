import psycopg2
from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def config(filename='sql/database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f"Could not read from file {filename}")

    return db


# # TODO: delete
# def connect():
#     conn = None
#     try:
#         params = config()

#         # TODO logging
#         print('Connecting to the PostgreSQL database...')
#         conn = psycopg2.connect(**params)

#         return conn
#     except (Exception, psycopg2.DatabaseError) as error:
#         print(error)
#         if conn is not None:
#             conn.close()
#             print('Database connection closed.')


# # TODO: delete
# def create_tables():
#     commands = [
#         """
#         CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
#         """,
#         """
#         CREATE TABLE users (
#             user_id UUID DEFAULT uuid_generate_v4 () PRIMARY KEY,
#             user_name VARCHAR(60) NOT NULL,
#             user_address VARCHAR(36)
#         )
#         """,
#         """CREATE TABLE credits (
#             credit_id SERIAL PRIMARY KEY,
#             credit_amount INTEGER NOT NULL,
#             credit_owner UUID NOT NULL REFERENCES users(user_id)
#         )
#         """,
#         # TODO should we use contract address as the key?
#         """
#         CREATE TABLE contracts (
#             contract_id SERIAL PRIMARY KEY,
#             contract_name VARCHAR(50) NOT NULL,
#             contract_address VARCHAR(36) NOT NULL,
#             contract_credit SERIAL NOT NULL REFERENCES credits(credit_id),
#             owner_id UUID NOT NULL REFERENCES users(user_id)
#         )
#         """,
#         # TODO: what's the maximum length of Michelson entrypoints?
#         """
#         CREATE TABLE entrypoints (
#             entrypoint_id SERIAL PRIMARY KEY,
#             entrypoint_name VARCHAR(50) NOT NULL,
#             contract_id SERIAL NOT NULL REFERENCES contracts(contract_id),
#             is_enabled BOOLEAN NOT NULL
#         )
#         """,
#         """
#         CREATE TABLE operations (
#             operation_id SERIAL PRIMARY KEY,
#             operation_cost INTEGER NOT NULL,
#             operation_target SERIAL NOT NULL REFERENCES contracts(contract_id),
#             operation_entrypoint SERIAL NOT NULL REFERENCES entrypoints(entrypoint_id)
#         )
#         """
#     ]
#     db = connect()
#     cur = db.cursor()
#     for command in commands:
#         cur.execute(command)

#     cur.close()
#     db.commit()



try:
    params = config()
    print(params)
    engine = create_engine(
        url=params['url']
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except (Exception) as e:
    print(e)
    pass

def get_db():
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
