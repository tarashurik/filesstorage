import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File as File_
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from auth import (
    authenticate_user,
    credentials_error,
    create_token,
    get_current_user
)
from schemas import UserRead, UserCreate, FileRead, FileCreate
from crud import UserCRUD, FileCRUD


users_router = APIRouter(prefix="/users", tags=["users"])
files_router = APIRouter(prefix="/files", tags=["files"])

logger = logging.getLogger(__name__)


def hash_file(file):
    logger.info(msg="Start hashing file")
    hash_md5 = hashlib.md5(file)
    file_hash = hash_md5.hexdigest()
    logger.info(msg="End hashing file")
    return file_hash


@users_router.post('/token')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), users: UserCRUD = Depends()):
    logger.info(msg="Start logining user")
    user = authenticate_user(form_data.username, form_data.password, users)
    if not user:
        logger.error(msg="Start logining user")
        raise credentials_error
    response = create_token(user.username)
    logger.info(msg="End logining user")
    return response


@users_router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(username: str = Form(...),
                      email: str = Form(...),
                      first_name: Optional[str] = Form(None),
                      last_name: Optional[str] = Form(None),
                      password: str = Form(...),
                      users: UserCRUD = Depends()):
    logger.info(msg="Start registering user")
    user = UserCreate(username=username,
                      email=email,
                      first_name=first_name,
                      last_name=last_name,
                      password=password)
    db_user = users.read_by_username(username=user.username)
    if db_user:
        logger.error(msg=f"User with username '{user.username}' already registered")
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    db_user = users.create(user)
    response = UserRead.from_orm(db_user)
    logger.info(msg="End registering user")
    return response


@users_router.get("/logined_user", response_model=UserRead)
async def get_login_user(current_user: UserRead = Depends(get_current_user)):
    return current_user


@users_router.get("/{username}", response_model=UserRead)
async def get_user(username: str, users: UserCRUD = Depends()):
    logger.info(msg=f"Try to find user '{username}'")
    db_user = users.read_by_username(username)
    if db_user is None:
        logger.error(msg=f"User '{username}' NOT found")
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    logger.info(msg=f"User '{username}' found")
    return UserRead.from_orm(db_user)


@files_router.post("/upload", response_model=FileRead)
async def upload_file(description: Optional[str] = Form(None),
                      file: UploadFile = File_(...),
                      files: FileCRUD = Depends(),
                      current_user: UserRead = Depends(get_current_user)
                      ):
    logger.info(msg="Start upload file")

    read_file = file.file.read()
    file_size_bytes = len(read_file)
    filehash = hash_file(read_file)

    file_data = FileCreate(description=description, file=file, file_size_bytes=file_size_bytes, filehash=filehash)
    db_file = files.create(file_data=file_data, current_user=current_user)
    logger.info(msg="End upload file")
    return FileRead.from_orm(db_file)


@files_router.get("/")
async def get_user_files(current_user: UserRead = Depends(get_current_user), files: FileCRUD = Depends()):
    db_files_dict = files.read_current_user_all_files(current_user=current_user)
    logger.debug(msg="Start encode content to JSON")
    content = jsonable_encoder(db_files_dict)
    logger.debug(msg="End encode content to JSON")
    return JSONResponse(content=content)


@files_router.delete("/{file_id}")
async def delete_file(file_id: int, current_user: UserRead = Depends(get_current_user), files: FileCRUD = Depends()):
    deleted_filename = files.delete_file_by_id(current_user=current_user, file_id=file_id)
    return f'File {deleted_filename} successfully deleted'
