from src import database


def clear_tables():
    commands = [
        "DROP TABLE IF EXISTS users CASCADE",
        "DROP TABLE IF EXISTS credits CASCADE",
        "DROP TABLE IF EXISTS entrypoints CASCADE",
        "DROP TABLE IF EXISTS contracts CASCADE",
        "DROP TABLE IF EXISTS operations CASCADE"
    ]

    db = database.connect()
    cur = db.cursor()
    for command in commands:
        cur.execute(command)

    cur.close()
    db.commit()


def insert_data():
    db = database.connect()
    cur = db.cursor()
    sql1 = """INSERT INTO users(user_name, user_address)
        VALUES(%s, %s) RETURNING user_id;"""
    user1 = ("Alfred", "tz1VLKbNYhmfyQSZzsdLWrbtVbyjsRf9qEjN")
    cur.execute(sql1, user1)
    user_id = cur.fetchone()[0]

    sql2 = """INSERT INTO credits(credit_amount, credit_owner)
        VALUES(%s, %s) RETURNING credit_id"""
    cur.execute(sql2, (int(1e8), user_id))
    credit_id = cur.fetchone()[0]

    sql3 = """INSERT INTO contracts(contract_address, contract_name, contract_credit, owner_id)
        VALUES(%s, %s, %s, %s) RETURNING contract_id;"""
    contract1 = ("KT1Re88VMEJ7TLHTkXSHQYZQTD3MP3k7j6Ar",
                 "NFT weapons",
                 credit_id,
                 user_id)
    cur.execute(sql3, contract1)
    contract1_id = cur.fetchone()[0]

    contract2 = ("KT1Rp1rgfwS25XrWU6fUnR8cw6KMZBhDvXdq",
                 "Staking contract",
                 credit_id,
                 user_id)
    cur.execute(sql3, contract2)
    contract2_id = cur.fetchone()[0]

    sql4 = """INSERT INTO entrypoints(entrypoint_name, contract_id, is_enabled)
        VALUES(%s, %s, %s)"""
    entrypoints = [
        ("mint_token", contract1_id, "true"),
        ("permit", contract1_id, "true"),
        ("stake", contract2_id, "true"),
        ("unstake", contract2_id, "true")
    ]
    for e in entrypoints:
        cur.execute(sql4, e)
    db.commit()
    cur.close()