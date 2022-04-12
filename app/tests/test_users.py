import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from dependencies import get_db
from database import Base


test_user_data = {
    "username": "admin",
    "email": "admin@admin.com",
    "first_name": None,
    "last_name": None,
    "password": "admin",
}


SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:postgres@0.0.0.0:5432/db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_user(test_db):
    response = client.post("/users/register", data=test_user_data)
    assert response.status_code == 201
