from fastapi import FastAPI

from . import models
from .database import engine
from .routers import users, posts, auth, files, none, likes




app = FastAPI()


# This Will Create All Models That we Define In Models File
models.Base.metadata.create_all(bind=engine)

app.include_router(users.router) # read all end-points in users file
app.include_router(posts.router) # read all end-points in posts file
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(likes.router)
app.include_router(none.router)