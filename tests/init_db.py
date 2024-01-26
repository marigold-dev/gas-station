from src import database, models
from sqlalchemy import text
import os


# truncate_db is used to clear all data from the tables with
# trigger handling
def truncate_db():
    con = database.engine.connect()
    trans = con.begin()
    for table in models.Base.metadata.sorted_tables:
        # For each table, disables triggers, deletes all rows from the table
        con.execute(text(f'ALTER TABLE "{table.name}" DISABLE TRIGGER ALL;'))
        con.execute(table.delete())
        # re-enable triggers
        con.execute(text(f'ALTER TABLE "{table.name}" ENABLE TRIGGER ALL;'))
    # commits the changes to the database
    trans.commit()

# insert_data is used to populate the database with data from an
# SQL file: ./sql/init_db.sql


def insert_data():
    session = database.SessionLocal()
    try:
        # contructs the path to the SQL file
        p = os.path.join(".", "sql", "init_db.sql")
        # open file and read the content
        with open(p) as file:
            query = text(file.read())
            # the content is executed as a SQL query
            session.execute(query)
            # changes are committed to the database
            session.commit()
    # session is closed in the finally block
    # to ensure proper cleanup
    finally:
        session.close()
