from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File as File_
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
# from uuid import UUID

from auth import (
    authenticate_user,
    credentials_error,
    create_token,
    get_current_user
)
from schemas import UserRead, UserCreate, FileRead, FileCreate
from crud import UserCRUD, FileCRUD, UPLOAD_DIR, MAX_SIZE_MB


users_router = APIRouter(prefix="/users", tags=["users"])
files_router = APIRouter(prefix="/files", tags=["files"])


@users_router.post('/token')
def login(form_data: OAuth2PasswordRequestForm = Depends(), users: UserCRUD = Depends()):
    user = authenticate_user(form_data.username, form_data.password, users)
    if not user:
        raise credentials_error
    return create_token(user.username)


@users_router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(username: str = Form(...),
                email: str = Form(...),
                first_name: Optional[str] = Form(None),
                last_name: Optional[str] = Form(None),
                password: str = Form(...),
                users: UserCRUD = Depends()):
    user = UserCreate(username=username,
                      email=email,
                      first_name=first_name,
                      last_name=last_name,
                      password=password)
    db_user = users.read_by_username(username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    db_user = users.create(user)
    return UserRead.from_orm(db_user)


@users_router.get("/logined_user", response_model=UserRead)
def get_login_user(current_user: UserRead = Depends(get_current_user)):
    return current_user


@users_router.get("/{username}", response_model=UserRead)
def get_user(username: str, users: UserCRUD = Depends()):
    db_user = users.read_by_username(username)
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return UserRead.from_orm(db_user)


@files_router.post("/upload", response_model=FileRead)
def upload_file(description: Optional[str] = Form(None),
                file: UploadFile = File_(...),
                files: FileCRUD = Depends(),
                current_user: UserRead = Depends(get_current_user)
                ):

    file_size_bytes = len(file.file.read())
    file_size_mb = file_size_bytes/(1024*1024)

    if file_size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Your file too big - {round(file_size_mb, 2)} MB, please, upload files less than {MAX_SIZE_MB} MB"
        )

    db_file = files.read_by_filename(filename=file.filename)

    if db_file and f'{db_file.file_dir}/{db_file.filename}' == f'{UPLOAD_DIR}/{current_user.id}/{db_file.filename}':
        raise HTTPException(
            status_code=400,
            detail="File with same name already uploaded"
        )

    file_data = FileCreate(description=description, file=file, file_size_bytes=file_size_bytes)
    db_file = files.create(file_data=file_data, current_user=current_user)
    return FileRead.from_orm(db_file)


@files_router.get("/")
def get_user_files(current_user: UserRead = Depends(get_current_user), files: FileCRUD = Depends()):
    db_files = files.read_current_user_all(current_user=current_user)
    if not list(db_files):
        raise HTTPException(
            status_code=404,
            detail="Files not found. There are no files in your repository"
        )
    files_dict = dict()
    for db_file in db_files:
        files_dict[db_file.filename] = FileRead.from_orm(db_file)
    content = jsonable_encoder(files_dict)
    return JSONResponse(content=content)


@files_router.delete("/{filename}")
def delete_file(filename: str, current_user: UserRead = Depends(get_current_user), files: FileCRUD = Depends()):
    db_files = files.read_current_user_all(current_user=current_user)
    if not list(db_files):
        raise HTTPException(
            status_code=404,
            detail="Files not found. There are no files in your repository"
        )
    for db_file in db_files:
        if db_file.filename == filename:
            files.delete_file_by_filename(current_user=current_user, filename=filename)
            return f'File {filename} successfully deleted'
    raise HTTPException(
        status_code=404,
        detail=f"File '{filename}' not found. There are no file with such name in your repository"
    )
