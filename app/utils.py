
from typing import Dict, Tuple
from passlib.context import CryptContext

pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hashing Password Dealears

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password,hashed_password)


def tuples_to_pydantic_model(keys: Tuple, values: Tuple) -> Dict:
    if len(keys) != len(values):
        raise

    dict_value = {}
    for i in range(len(keys)):
        dict_value[keys[i]] = values[i]
    
    return dict_value