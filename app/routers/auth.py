from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..database import get_db
from ..schemas import tokenSchema
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES

from .auth_utils import *

router = APIRouter(
    prefix='/auth',
    tags= ['Authentication']
)


# [*] Generate Form via [OAuth2PasswordRequestForm]
# [*] the data that send Shold be in Form not JSON
# [*] as we Know, Fastapi Serializer Automatically Pytdantic object into JSON
@router.post("/token/")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> tokenSchema.Tokens:
    """
    handle login process.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await create_access_token(
        data={"id": user.id, "email": user.email}
    )

    refresh_token = await create_refresh_token(user.id)

    return tokenSchema.Tokens(access_token=access_token, refresh_token=refresh_token, token_type='bearer')


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)) -> tokenSchema.AccessToken:
    payload = await validate_refresh_token(refresh_token)
    user_id = payload.get("id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = await create_access_token(
        data={"id": user.id, "email": user.email}, expires_delta=access_token_expires
    )
    return tokenSchema.AccessToken(access_token=new_access_token, token_type='bearer')






