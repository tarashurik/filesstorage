import uvicorn
from fastapi import FastAPI

from database import Base, engine
from routers import router as app_router


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(app_router)

# if __name__ == '__main__':
#     reload_dirs = ['./..']
#     uvicorn.run('main:app', reload=True, reload_dirs=reload_dirs)
