import os
import shutil

from fastapi.params import Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional, List
from dotenv import load_dotenv

from models import User, File
from dependencies import get_db
from schemas import UserCreate, UserRead, FileCreate

load_dotenv()

UPLOAD_DIR = os.environ.get('UPLOAD_FILES_DIR')
MAX_SIZE_MB = int(os.environ.get('MAX_SIZE_UPLOADED_FILES_MB'))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCRUD:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def read_by_id(self, user_id: int) -> Optional[User]:
        query = self.db.query(User)
        return query.filter(User.id == user_id).first()

    def read_by_username(self, username: str) -> Optional[User]:
        query = self.db.query(User)
        return query.filter(User.username == username).first()

    @staticmethod
    def get_hashed_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password, hashed_password) -> bool:
        return pwd_context.verify(password, hashed_password)

    def create(self, user: UserCreate) -> User:
        hashed_password = self.get_hashed_password(user.password)

        db_user = User(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            hashed_password=hashed_password
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user


class FileCRUD:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def read_current_user_all(self, current_user: UserRead) -> Optional[List[File]]:
        query = self.db.query(File)
        return query.filter(File.owner_id == current_user.id)

    def read_by_id(self, file_id: int) -> Optional[File]:
        query = self.db.query(File)
        return query.filter(File.id == file_id).first()

    def read_by_filename(self, filename: str) -> Optional[File]:
        query = self.db.query(File)
        return query.filter(File.filename == filename).first()

    def delete_file_by_filename(self, current_user: UserRead, filename: str) -> None:
        file_to_delete = self.db.query(File).filter(File.owner_id == current_user.id, File.filename == filename)
        file_to_delete.delete()
        self.db.commit()

    def create(self, file_data: FileCreate, current_user: UserRead) -> File:

        db_file = File(
            filename=file_data.file.filename,
            file_dir=f'{UPLOAD_DIR}/{current_user.id}',
            description=file_data.description,
            owner_id=current_user.id,
            content_type=file_data.file.content_type,
            file_size_bytes=file_data.file_size_bytes
        )

        if not os.path.exists(UPLOAD_DIR):
            os.mkdir(UPLOAD_DIR)
        if not os.path.exists(db_file.file_dir):
            os.mkdir(db_file.file_dir)
        with open(f'{db_file.file_dir}/{db_file.filename}', 'wb') as new_file:
            shutil.copyfileobj(file_data.file.file, new_file)

        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)

        return db_file
