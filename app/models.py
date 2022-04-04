from uuid import uuid4

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(20))
    email = Column(String(50), unique=True, index=True)
    first_name = Column(String(20), nullable=True)
    last_name = Column(String(20), nullable=True)
    password = Column(String)
    # hashed_password = Column(String)

    files = relationship("File", back_populates="owner")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    description = Column(String)
    owner_id = Column(UUID, ForeignKey("users.id"))

    owner = relationship("User", back_populates="files")


