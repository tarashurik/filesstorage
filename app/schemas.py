from typing import Optional

from pydantic import BaseModel
from uuid import UUID


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    # id: UUID
    id: int
    hashed_password: str

    class Config:
        orm_mode = True


class FileBase(BaseModel):
    description: Optional[str] = None


class FileCreate(FileBase):
    pass


class FileRead(FileBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True
