from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.utils import ConfigurationError


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

try:
    params = config()
    url = f"postgresql://{params['user']}:{params['password']}@{params['host']}:5432/{params['database']}"
    engine = create_engine(
        url=url,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except (Exception) as e:
    print(e)
    raise ConfigurationError("Cannot connect to database.")

def get_db():
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
