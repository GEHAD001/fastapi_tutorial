from asyncio import gather
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError
import jwt


from datetime import datetime, timedelta, timezone

from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY,oauth2_scheme
from .. import models, utils
from ..database import get_db
from typing import Annotated, Dict
from redis import Redis

# [*] not decalred in our model
# async def get_current_active_user(
#     current_user: Annotated[models.User, Depends(get_current_user)],
# ):
#     if current_user.disabled:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user

async def generate_tokens(data: dict, redis_cli: Redis):
    encode_to_access_task, encode_to_refresh_task = __encode_to_access(data), __encode_to_refresh(data)

    access_token, refresh_token = await gather(encode_to_access_task, encode_to_refresh_task)

    # Store In Redis
    store_in_redis(redis_cli, data.get('id'), access_token, refresh_token)
    return access_token, refresh_token


async def __encode_to_access(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def __encode_to_refresh(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def store_in_redis(redis_cli, id, access_token, refresh_token) -> None:
    access_token_name = f"{id}:access_token:{access_token}"
    refresh_token_name = f"{id}:refresh_token:{refresh_token}"

    pipeline = redis_cli.pipeline()

    pipeline.setex(name=access_token_name, value='', time=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    pipeline.setex(name=refresh_token_name, value='', time=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    pipeline.execute()
    return 

async def validate_refresh_token(refresh_token: str, r: Redis) -> Dict | None:
    """
    decode then check refresh token expirations, return payload or raise an exception.
    """ 
    try:
        if not r.keys(f'*{refresh_token}'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
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
    check access token validation, then return user of the token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Check if token is valid in Redis cache
        in_redis = await check_token_in_redis(token)
        if not in_redis:
            raise credentials_exception
        
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("email")

        # Fetch user from database
        user = db.query(models.User).filter(models.User.email == email).first()

        if user is None:
            raise credentials_exception
        
        return user

    except jwt.InvalidTokenError:
        raise credentials_exception
    
    except ValidationError as e:
        raise e
    
    
async def check_token_in_redis(token: str) -> bool:
    """
    Check if token exists in Redis.
    """  
    from app.main import app
    redis_cli: Redis = app.state.redis_cli
    return bool(redis_cli.keys(f"*:{token}"))


async def create_access_token(data: dict, redis_cli: Redis) -> str:
    """
    pass the data that want to embedded in token, then will generate new access token and store it in redis.
    """
    # [1] Setup Access Token
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # # [2] Store In Redis
    name=f"{data.get('id')}:access_token:{token}"
    redis_cli.setex(name=name, value='', time=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
 
    return token

#! Not Used For Know 
async def create_refresh_token(data: dict, redis_cli: Redis) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire})
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Store In Redis
    name=f"{data.get('id')}:refresh_token:{token}"
    redis_cli.setex(name=name, value='', time=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    return token