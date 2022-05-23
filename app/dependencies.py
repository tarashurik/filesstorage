from functools import lru_cache

import config
import database


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache
def get_db_settings() -> config.DBSettings:
    return config.DBSettings()
