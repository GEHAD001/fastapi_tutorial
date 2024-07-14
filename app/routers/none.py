from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Annotated, Any
from redis import Redis

from app import models
from app.database import get_db, Base
# from ..main import redis_connection

router = APIRouter(prefix="/none",tags=['None'])


# Fastapi Convert Object Model Automatically ? Yes Even Without Pydantic [Not All Cause, Convert When only use One Model in query method]
@router.get('/')
async def is_convert(db: Session = Depends(get_db)):
    query = db.query(models.User).all()

    response = {
        "count": len(query),
        "users": query
    }
    return response



@router.get('/stuff')
async def stuff():
    print([c.name for c in models.User.__table__.columns])
    return ''

from app import utils
@router.get('/redis-connecting')
async def redis_is_connection(request: Request, db: Session = Depends(get_db)):
    return ''

