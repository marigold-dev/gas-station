from src import database, models
from sqlalchemy import text
import os


def truncate_db():
    con = database.engine.connect()
    trans = con.begin()
    for table in models.Base.metadata.sorted_tables:
        con.execute(text(f'ALTER TABLE "{table.name}" DISABLE TRIGGER ALL;'))
        con.execute(table.delete())
        con.execute(text(f'ALTER TABLE "{table.name}" ENABLE TRIGGER ALL;'))
    trans.commit()


def insert_data():
    session = database.SessionLocal()
    try:
        p = os.path.join(".", "sql", "init_db.sql")
        with open(p) as file:
            query = text(file.read())
            session.execute(query)
            session.commit()
    finally:
        session.close()
