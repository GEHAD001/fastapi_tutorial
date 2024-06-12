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

# ==========================================================================================

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

async def validate_refresh_token(refresh_token: str) -> Dict | None:
    """
    decode then check refresh token expirations, return payload or raise an exception.
    """
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
