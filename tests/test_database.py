from tests import init_db
from src import database


def test_foo():
    init_db.truncate_db()
    init_db.insert_data()
