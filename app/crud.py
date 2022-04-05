from typing import List
from uuid import UUID

from fastapi.params import Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models import User
from dependencies import get_db
from schemas import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCRUD:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # def read(self, uuid: UUID) -> User:
    def read(self, user_id: int) -> User:
        query = self.db.query(User)
        return query.filter(User.id == user_id).first()

    def read_by_username(self, username: str):
        query = self.db.query(User)
        return query.filter(User.username == username).first()

    # def read_all(self, skip: int = 0, max: int = 100) -> List[User]:
    #     query = self.db.query(User)
    #     return query.offset(skip).limit(max).all()

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
