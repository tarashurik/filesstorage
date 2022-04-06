from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dependencies import get_db_settings

settings = get_db_settings()

SQLALCHEMY_DATABASE_URL = \
    f"postgresql://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
#
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
