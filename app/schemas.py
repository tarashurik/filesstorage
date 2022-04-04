from typing import Optional

from pydantic import BaseModel
from uuid import UUID


class UserBase(BaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: UUID

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
