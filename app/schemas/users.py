from pydantic import BaseModel, EmailStr

class GetUser(BaseModel):
    id: int
    name: str
    email: EmailStr


class UpdateUser(BaseModel):
    