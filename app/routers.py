from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File as File_
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from uuid import UUID

from auth import (
    authenticate_user,
    credentials_error,
    create_token,
    get_current_user
)
from schemas import UserRead, UserCreate, FileRead, FileCreate
from crud import UserCRUD, FileCRUD, UPLOAD_DIR


users_router = APIRouter(prefix="/users", tags=["users"])
files_router = APIRouter(prefix="/files", tags=["files"])


# @router.get("/", response_model=List[UserRead])
# def list_speedsters(skip: int = 0, max: int = 10, speedsters: UserCRUD = Depends()):
#     db_speedsters = speedsters.all(skip=skip, max=max)
#     return parse_obj_as(List[UserRead], db_speedsters)

@users_router.post('/token')
def login(form_data: OAuth2PasswordRequestForm = Depends(), users: UserCRUD = Depends()):
    user = authenticate_user(form_data.username, form_data.password, users)
    if not user:
        raise credentials_error
    return create_token(user.username)


@users_router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, users: UserCRUD = Depends()):
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
    print(current_user)
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
    db_file = files.read_by_filename(filename=file.filename)

    if db_file and f'{db_file.file_dir}/{db_file.filename}' == f'{UPLOAD_DIR}/{current_user.id}/{db_file.filename}':
        raise HTTPException(
            status_code=400,
            detail="File with same name already uploaded"
        )

    file_data = FileCreate(description=description, file=file)
    db_file = files.create(file_data=file_data, current_user=current_user)
    return FileRead.from_orm(db_file)
