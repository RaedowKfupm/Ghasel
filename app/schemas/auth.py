from pydantic import BaseModel, EmailStr
from app.core.enums import UserRole

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole

class UserLogin(BaseModel):
    password: str
    email: EmailStr

class ResponseUser(BaseModel):
    access_token: str
    token_type: str
    name: str
    email: EmailStr
    role: UserRole