import time
import logging

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from database import Base, engine
from routers import users_router, files_router

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

while True:
    try:
        logger.info("Try connect to DataBase")
        Base.metadata.create_all(bind=engine)
        logger.info("Connection to DataBase successful")
        break
    except OperationalError:
        logger.warning("DataBase hasn't ready yet, try again in 1 second")
        time.sleep(1)
        continue

app = FastAPI()
app.include_router(users_router)
app.include_router(files_router)
