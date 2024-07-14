from asyncio import gather
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status, HTTPException, Response
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

import time
# [*] Generate Form via [OAuth2PasswordRequestForm]
# [*] the data that send Shold be in Form not JSON
# [*] as we Know, Fastapi Serializer Automatically Pytdantic object into JSON
@router.post("/token/")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> tokenSchema.Tokens:
    """
    handle login process.
    """
    print('start execution')
    user = await authenticate_user(db, form_data.username, form_data.password)
    time.sleep(2)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    data = {"id": user.id, "email": user.email}
    access_token, refresh_token = await generate_tokens(data, request.app.state.redis_cli)
    print('end execution')
    return tokenSchema.Tokens(access_token=access_token, refresh_token=refresh_token, token_type='bearer')


@router.post("/refresh")
async def refresh_token(request: Request, refresh_token: str, db: Session = Depends(get_db)) -> tokenSchema.AccessToken:
    payload = await validate_refresh_token(refresh_token, request.app.state.redis_cli)
    access_token = await create_access_token(
        data=payload,
        redis_cli=request.app.state.redis_cli
    )
    return tokenSchema.AccessToken(access_token=access_token, token_type='bearer')
