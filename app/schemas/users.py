
from pydantic import BaseModel, EmailStr

class GetUser(BaseModel):
    id: int
    name: str
    email: EmailStr
    



class UpdateUser(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None