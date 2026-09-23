from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password_hash: str
    role: str
    phone_number: str

class UserLogin(BaseModel)
    password_hash: str
    email: EmailStr

class ResponseUser(BaseModel):
    access_token: str
    token_type: str
    name: str
    email: EmailStr
    role: str