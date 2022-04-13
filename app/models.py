from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(20), unique=True, index=True)
    email = Column(String(50))
    first_name = Column(String(20), nullable=True)
    last_name = Column(String(20), nullable=True)
    hashed_password = Column(String)

    files = relationship("File", back_populates="owner")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    filename = Column(String)
    file_dir = Column(String)
    description = Column(String(100))
    owner_id = Column(Integer, ForeignKey("users.id"))
    content_type = Column(String)
    file_size_bytes = Column(String)
    filehash = Column(String)

    owner = relationship("User", back_populates="files")
