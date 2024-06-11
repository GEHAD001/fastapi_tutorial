from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/none",tags=['None'])


# Fastapi Convert Object Model Automatically ? Yes Even Without Pydantic
@router.get('/')
async def is_convert(db: Session = Depends(get_db)):
    query = db.query(models.User).all()
    response = {
        "count": len(query),
        "users": query
    }
    return response