from typing import Annotated
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session

from app.routers.auth_utils import get_user_from_token


from .. import models, utils
from ..database import get_db
from ..schemas import userSchemas


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Users End-Point

@router.post('', status_code=status.HTTP_201_CREATED, response_model=userSchemas.UserCreateResponse)
async def create_user(user: Annotated[models.User, Depends(get_user_from_token)], payload: userSchemas.UserCreate,db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"user with email {payload.email} already exisit.")
    
    payload.password = utils.get_password_hash(payload.password)

    user_object = models.User(**payload.model_dump())
    db.add(user_object)
    db.commit()
    db.refresh(user_object)
    return user_object

@router.get('')
async def get_all_users(user: Annotated[models.User, Depends(get_user_from_token)], db: Session = Depends(get_db)) -> list[userSchemas.UserResponse]:
    users = db.query(models.User).all()
    return users


@router.get('/{id}', response_model=userSchemas.UserResponse)
async def get_user(id: int, db: Session = Depends(get_db)) -> userSchemas.UserResponse:
    user : dict | None = db.query(models.User).get(id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id {id} doesn't exisit")
    return user

    
@router.get('/me/')
def read_user_me(user: Annotated[models.User, Depends(get_user_from_token)]) -> userSchemas.UserResponse:
    return user
