from pydantic import BaseModel, EmailStr


class UserCredentilas(BaseModel):
    email: EmailStr
    password: str

# Provided Token When Login
class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Embedded Data in Token
class TokenData(BaseModel):
    id: int | str
    email: EmailStr | None = None

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class RefreshToken(BaseModel):
    refresh_token: str