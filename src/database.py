import psycopg2
from configparser import ConfigParser


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


# TODO: with block
def connect():
    conn = None
    try:
        params = config()

        # TODO logging
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)

        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        if conn is not None:
            conn.close()
            print('Database connection closed.')


def create_tables():
    commands = [
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
        """,
        """
        CREATE TABLE users (
            user_id UUID DEFAULT uuid_generate_v4 () PRIMARY KEY,
            user_name VARCHAR(60) NOT NULL,
            user_address VARCHAR(36)
        )
        """,
        """CREATE TABLE credits (
            credit_id SERIAL PRIMARY KEY,
            credit_amount INTEGER NOT NULL,
            credit_owner UUID NOT NULL REFERENCES users(user_id)
        )
        """,
        # TODO should we use contract address as the key?
        """
        CREATE TABLE contracts (
            contract_id SERIAL PRIMARY KEY,
            contract_name VARCHAR(50) NOT NULL,
            contract_address VARCHAR(36) NOT NULL,
            contract_credit SERIAL NOT NULL REFERENCES credits(credit_id),
            owner_id UUID NOT NULL REFERENCES users(user_id)
        )
        """,
        # TODO: what's the maximum length of Michelson entrypoints?
        """
        CREATE TABLE entrypoints (
            entrypoint_id SERIAL PRIMARY KEY,
            entrypoint_name VARCHAR(50) NOT NULL,
            contract_id SERIAL NOT NULL REFERENCES contracts(contract_id),
            is_enabled BOOLEAN NOT NULL
        )
        """,
        """
        CREATE TABLE operations (
            operation_id SERIAL PRIMARY KEY,
            operation_cost INTEGER NOT NULL,
            operation_target SERIAL NOT NULL REFERENCES contracts(contract_id),
            operation_entrypoint SERIAL NOT NULL REFERENCES entrypoints(entrypoint_id)
        )
        """
    ]
    db = connect()
    cur = db.cursor()
    for command in commands:
        cur.execute(command)

    cur.close()
    db.commit()


def find(command):
    db = connect()
    cur = db.cursor()
    cur.execute(command)
    res = cur.fetchall()
    cur.close()
    db.close()
    return res


def find_contract(contract_address):
    return find(f"SELECT contract_id \
                FROM contracts WHERE contract_address='{contract_address}'")


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

if __name__ == '__main__':
    connect()
