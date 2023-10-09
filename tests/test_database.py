from tests import init_db
from src import database


def test_foo():
    init_db.clear_tables()
    database.create_tables()
    init_db.insert_data()
