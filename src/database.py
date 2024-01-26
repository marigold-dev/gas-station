from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .utils import ConfigurationError
from .config import logging

# This function reads database connection parameters from a configuration
# sql/database.ini


def config(filename="sql/database.ini", section="postgresql"):
    # parse the configuratiion file
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    # if the specific section (postgresql) exists in the
    # configuration file, it extracts the parameters
    # and returns them as a dictionary
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    # otherwise, it raises an exception
    else:
        raise Exception(f"Could not read from file {filename}")
    return db


try:
    # retrieve database connection paramaters
    params = config()
    # the parameters are used to construct the database URL
    url = f"postgresql://{params['user']}:{params['password']}@{params['host']}:5432/{params['database']}"
    # SQL engine is created with the constructed URL
    engine = create_engine(
        url=url,
    )
    # A session factory is created bound to the engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
# error handling, if an error occurs during database configuration, it logs the error
# using the logging module and raises an error message
except Exception as e:
    logging.error(f"Error occurred on database configuration : {e}")
    raise ConfigurationError("Cannot connect to database.")


# Database session management
def get_db():
    if SessionLocal:
        db = SessionLocal()
        try:
            # it yields a session `db` from SessionLocal
            yield db
        finally:
            # the session is automatically closed when exiting the function
            db.close()
