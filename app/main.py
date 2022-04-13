import time

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from database import Base, engine
from routers import users_router, files_router


while True:
    try:
        Base.metadata.create_all(bind=engine)
        break
    except OperationalError:
        print("DataBase hasn't ready yet, try again in 1 second")
        time.sleep(1)
        continue

app = FastAPI()
app.include_router(users_router)
app.include_router(files_router)
