import os
from dotenv import load_dotenv
import inject
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(".env")

from domains.example.repositories import ExampleRepository, IExampleRepository
from infrastructures.database.factories import (
    ConnectionStringFactory,
    IConnectionStringFactory,
)
connection_string_factory = ConnectionStringFactory(
    os.environ.get("POSTGRES_HOST"),
    os.environ.get("POSTGRES_PORT"),
    os.environ.get("POSTGRES_DB"),
    os.environ.get("POSTGRES_USER"),
    os.environ.get("POSTGRES_PASSWORD")
)

def _create_session_maker(factory: IConnectionStringFactory) -> sessionmaker:
    connection_string = factory.create()
    engine = create_engine(connection_string)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def di_config(binder):
    binder.bind(IExampleRepository, ExampleRepository())
    binder.bind(IConnectionStringFactory, connection_string_factory)
    # session_maker = _create_session_maker(connection_string_factory)
    # binder.bind(sessionmaker, session_maker)


def configure_injector():
    if not inject.get_injector():
        inject.configure(di_config)
    else:
        print("Injector is already configured")
