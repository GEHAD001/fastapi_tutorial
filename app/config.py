from pathlib import Path
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings
from os import path


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_name: str
    database_username: str
    database_password: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    
    redis_hostname: str
    redis_password: str
    redis_port: int

    class Config:
        env_file = 'fastapi_app\.env'


settings = Settings()

# JWT
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

# REDIS CONNECTION
REDIS_HOSTNAME = settings.redis_hostname
REDIS_PASSWORD = settings.redis_password
REDIS_PORT = settings.redis_port

# DIR MANAGMENT
#! New: Create Upload Automatically Even if Deleted
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True) 


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token/")