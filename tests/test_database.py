from tests import init_db
from src import database

# Test case for initializing a database
def test_foo():
    # to truncate (clear) the database tables
    init_db.truncate_db()
    # to inseart data into the database
    init_db.insert_data()
    print("Data inserted.")
