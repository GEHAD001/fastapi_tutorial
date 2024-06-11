from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError
import jwt

from datetime import datetime, timedelta, timezone
from app.schemas.tokenSchema import  TokenData

from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY,oauth2_scheme
from .. import models, utils
from ..database import get_db
from typing import Annotated

# [*] not decalred in our model
# async def get_current_active_user(
#     current_user: Annotated[models.User, Depends(get_current_user)],
# ):
#     if current_user.disabled:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user


async def create_access_token(data: dict, expires_delta: timedelta |  None = None) -> str:
    """
    pass the data that want to embedded in token, then will generate new access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_refresh_token(user_id: int) -> str:
    to_encode = {"id": user_id}
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def validate_refresh_token(refresh_token: str) -> None:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")



async def authenticate_user(db: Session, email: str, password: str) -> bool | models.User  :
    """
    return False if the given credintailas are wrong
    """
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not utils.verify_password(password, user.password):
        return False
    return user

async def get_user_from_token(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]):
    """
    return user of the token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(id = payload.get('id'), email=email)

    except jwt.InvalidTokenError:
        raise credentials_exception
    
    except ValidationError as e:
        raise e
    
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if user is None:
        raise credentials_exception
    return user

# ======================================================================

# [*] I think this depends -> (epends(oauth2_scheme)) are return the exisist access token


