from pydantic import BaseModel, EmailStr

from app.core.enums import UserRole
from app.schemas.fields import Password, PersonName


class UserRegister(BaseModel):
    name: PersonName
    email: EmailStr
    password: Password
    role: UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ResponseUser(BaseModel):
    access_token: str
    token_type: str
    name: str
    email: EmailStr
    role: UserRole
