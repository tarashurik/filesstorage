import hashlib
import os
import shutil
import logging

from fastapi import HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional
from dotenv import load_dotenv

from models import User, File
from dependencies import get_db
from schemas import UserCreate, UserRead, FileCreate, FileRead

load_dotenv()
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.environ.get('UPLOAD_FILES_DIR')
MAX_SIZE_MB = int(os.environ.get('MAX_SIZE_UPLOADED_FILES_MB'))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_file(file):
    logger.info(msg="Start hashing file")
    hash_md5 = hashlib.md5(file)
    file_hash = hash_md5.hexdigest()
    logger.info(msg="End hashing file")
    return file_hash


class UserCRUD:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def read_by_id(self, user_id: int) -> Optional[User]:
        query = self.db.query(User)
        return query.filter(User.id == user_id).one_or_none()

    def read_by_username(self, username: str) -> Optional[User]:
        query = self.db.query(User)
        return query.filter(User.username == username).one_or_none()

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

    def read_current_user_all_files(self, current_user: UserRead) -> Optional[dict]:
        logger.info(msg="Start reading current user's all files")
        db_files = self.db.query(File).filter(File.owner_id == current_user.id).all()
        db_files_dict = {db_file.filename: FileRead.from_orm(db_file) for db_file in db_files}
        if not db_files_dict:
            logger.error(msg="Files not found. There are no files in user's repository")
            raise HTTPException(
                        status_code=404,
                        detail="Files not found. There are no files in your repository"
                    )
        logger.info(msg="End reading current user's all files")
        return db_files_dict

    def read_by_id(self, file_id: int) -> Optional[File]:
        query = self.db.query(File)
        return query.filter(File.id == file_id).one_or_none()

    def read_by_filehash(self, filehash: str) -> Optional[File]:
        query = self.db.query(File)
        return query.filter(File.filehash == filehash).one_or_none()

    def delete_file_by_id(self, current_user: UserRead, file_id: int):
        logger.info(msg=f"Start deleting file with id={file_id}")
        file_to_delete_query = self.db.query(File).filter(File.owner_id == current_user.id, File.id == file_id)
        file_to_delete = file_to_delete_query.one_or_none()
        if not file_to_delete:
            logger.error(msg=f"File with id={file_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"File with id={file_id} not found. There are no file with such id in your repository"
            )
        filename = file_to_delete.filename
        file_to_delete_query.delete()
        self.db.commit()
        os.remove(f'{UPLOAD_DIR}/{current_user.id}/{filename}')
        logger.info(msg=f"End deleting file with id={file_id}")
        return filename

    async def create(self, file_data: FileCreate, current_user: UserRead) -> File:
        logger.info(msg="Start saving file")
        logger.info(msg="Start reading file")
        read_file = await file_data.file.read()
        logger.info(msg="End reading file")

        file_size_bytes = len(read_file)
        filehash = hash_file(read_file)

        db_file = File(
            filename=file_data.file.filename,
            file_dir=f'{UPLOAD_DIR}/{current_user.id}',
            description=file_data.description,
            owner_id=current_user.id,
            content_type=file_data.file.content_type,
            file_size_bytes=file_size_bytes,
            filehash=filehash
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
