# User Schema
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True

#* PAYLOAD VALIDATOR

class UserCreate(UserBase):
    password: str

    @field_validator('password')
    def password_validator(value):
        if len(value) < 7:
            raise ValueError("Password Should Contain at Leaset 8 Character")

        return value

# class UserPatch(BaseModel):
#     id: int
#     email: EmailStr | None
#     password: str | None


#     @field_validator('password')
#     def password_validator(value):
#         if len(value) < 7:
#             raise ValueError("Password Should Contain at Leaset 8 Character")

#         return value


#* RESPONSE VALIDATOR

class UserCreateResponse(UserBase):
    id: int

class UserResponse(UserBase):
    id: int
    created_at: datetime
