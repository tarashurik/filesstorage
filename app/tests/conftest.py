import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listens_for
from passlib.context import CryptContext

from auth import create_token
from main import app
from dependencies import get_db
from database import Base
from models import User


TEST_USER_DATA = {
    "username": "admin",
    "email": "admin@admin.com",
    "first_name": None,
    "last_name": None,
    "password": "admin",
}
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:postgres@0.0.0.0:5432/db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture()
def session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(session):
    def override_get_db():
        yield session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture()
def add_user(session):
    user_data = TEST_USER_DATA.copy()
    hashed_password = pwd_context.hash(user_data.pop("password"))
    user_data['hashed_password'] = hashed_password
    db_user = User(**user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)


@pytest.fixture()
def user_token() -> str:
    return create_token(
        TEST_USER_DATA["username"]
    )['access_token']
