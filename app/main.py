from fastapi import Depends, FastAPI
import redis
import httpx

from . import models
from .database import engine
from .routers import users, posts, auth, files, none, likes
from .config import REDIS_HOSTNAME, REDIS_PASSWORD, REDIS_PORT


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    app.state.redis_cli = redis.Redis(host=REDIS_HOSTNAME, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
    app.state.http_client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    app.state.redis_cli.close()

app.include_router(users.router)
app.include_router(posts.router) 
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(likes.router)
app.include_router(none.router)