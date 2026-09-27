from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str

class UserLogin(BaseModel):
    password: str
    email: EmailStr

class ResponseUser(BaseModel):
    access_token: str
    token_type: str
    name: str
    email: EmailStr
    role: str