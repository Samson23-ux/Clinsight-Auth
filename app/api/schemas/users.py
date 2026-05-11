from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBaseV1(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    email: EmailStr
    first_name: str
    last_name: str


class UserCreateV1(UserBaseV1):
    password: str = Field(..., min_length=8)


class UserOutV1(UserBaseV1):
    is_active: bool
    is_verified: bool
    created_at: datetime


class BaseResponseV1(BaseModel):
    status: str = "success"


class UserResponseV1(BaseResponseV1):
    data: UserOutV1
