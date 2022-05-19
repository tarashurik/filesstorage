import os
import shutil
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
from models import User, File
from routers import hash_file


TEST_USER_DATA = {
    "username": "admin",
    "email": "admin@admin.com",
    "first_name": None,
    "last_name": None,
    "password": "admin",
}
TEST_FILE_PATH = 'files_to_upload'
UPLOAD_DIR = 'media'

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:postgres@db/db"

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


@pytest.fixture()
def add_simple_file(add_user, session):
    with open(f'{TEST_FILE_PATH}/simple_file.txt', 'rb') as file:
        current_user = session.query(User).filter(User.username == TEST_USER_DATA['username']).first()
        db_file = File(
            filename=file.name.split('/')[1],
            file_dir=f'{UPLOAD_DIR}/{current_user.id}',
            description=None,
            owner_id=current_user.id,
            content_type='text',
            file_size_bytes=file.__sizeof__(),
            filehash=hash_file(file.read())
        )

        if not os.path.exists(UPLOAD_DIR):
            os.mkdir(UPLOAD_DIR)
        if not os.path.exists(db_file.file_dir):
            os.mkdir(db_file.file_dir)
        with open(f'{db_file.file_dir}/{db_file.filename}', 'wb') as new_file:
            shutil.copyfileobj(file, new_file)

    session.add(db_file)
    session.commit()
    session.refresh(db_file)
