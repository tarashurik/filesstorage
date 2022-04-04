from typing import List
from uuid import UUID

from fastapi.params import Depends
from sqlalchemy.orm import Session

from models import User
from dependencies import get_db
from schemas import UserCreate


class UserCRUD:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def read(self, uuid: UUID) -> User:
        query = self.db.query(User)
        return query.filter(User.id == uuid).first()

    def read_by_email(self, email: str):
        query = self.db.query(User)
        return query.filter(User.email == email).first()

    # def read_all(self, skip: int = 0, max: int = 100) -> List[User]:
    #     query = self.db.query(User)
    #     return query.offset(skip).limit(max).all()

    def create(self, user: UserCreate) -> User:
        faked_pass_hash = user.password + "__you_must_hash_me"  # todo hash

        db_user = User(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            password=faked_pass_hash
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user
