from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import parse_obj_as
from typing import List
from uuid import UUID

from schemas import UserRead, UserCreate
from crud import UserCRUD


router = APIRouter(prefix="/users", tags=["users"])


# @router.get("/", response_model=List[UserRead])
# def list_speedsters(skip: int = 0, max: int = 10, speedsters: UserCRUD = Depends()):
#     db_speedsters = speedsters.all(skip=skip, max=max)
#     return parse_obj_as(List[UserRead], db_speedsters)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, users: UserCRUD = Depends()):
    db_user = users.read_by_email(email=user.email)

    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    db_user = users.create(user)
    return UserRead.from_orm(db_user)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, users: UserCRUD = Depends()):
    db_user = users.read(user_id)

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return UserRead.from_orm(db_user)
