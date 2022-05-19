import os
import shutil
import logging

from fastapi import HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional, List
from dotenv import load_dotenv

from models import User, File
from dependencies import get_db
from schemas import UserCreate, UserRead, FileCreate

load_dotenv()
logger = logging.getLogger(__name__)

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

    # def read_by_filename(self, filename: str) -> Optional[File]:
    #     query = self.db.query(File)
    #     return query.filter(File.filename == filename).first()

    def read_by_filehash(self, filehash: str) -> Optional[File]:
        query = self.db.query(File)
        return query.filter(File.filehash == filehash).first()

    def delete_file_by_id(self, current_user: UserRead, id: int) -> None:
        file_to_delete = self.db.query(File).filter(File.owner_id == current_user.id, File.id == id)
        filename = file_to_delete[0].filename
        file_to_delete.delete()
        self.db.commit()
        os.remove(f'{UPLOAD_DIR}/{current_user.id}/{filename}')
        return filename

    def create(self, file_data: FileCreate, current_user: UserRead) -> File:
        logger.info(msg="Start saving file")
        db_file = File(
            filename=file_data.file.filename,
            file_dir=f'{UPLOAD_DIR}/{current_user.id}',
            description=file_data.description,
            owner_id=current_user.id,
            content_type=file_data.file.content_type,
            file_size_bytes=file_data.file_size_bytes,
            filehash=file_data.filehash
        )

        file_size_mb = db_file.file_size_bytes / (1024 * 1024)
        if file_size_mb > MAX_SIZE_MB:
            logger.error(msg=f"File too big - {round(file_size_mb, 2)} MB, max size is {MAX_SIZE_MB} MB")
            raise HTTPException(
                status_code=422,
                detail=f"Your file too big - {round(file_size_mb, 2)} MB,"
                       f" please, upload files less than {MAX_SIZE_MB} MB"
            )

        file_by_filehash = self.read_by_filehash(filehash=db_file.filehash)
        if file_by_filehash:
            logger.error(msg="File with same content have already uploaded")
            raise HTTPException(
                status_code=400,
                detail="You already have File with same content"
            )

        logger.debug(msg="File checking successful, making folder to upload")
        if not os.path.exists(UPLOAD_DIR):
            os.mkdir(UPLOAD_DIR)
        if not os.path.exists(db_file.file_dir):
            os.mkdir(db_file.file_dir)
        logger.debug(msg="Folder to upload created")
        logger.debug(msg="Saving file to upload folder")
        with open(f'{db_file.file_dir}/{db_file.filename}', 'wb') as new_file:
            shutil.copyfileobj(file_data.file.file, new_file)
        logger.debug(msg="File saved to folder, saving record to DataBase")
        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)
        logger.debug(msg="Record to DataBase created")
        logger.info(msg="End saving file")

        return db_file
