
from pydantic import BaseModel, EmailStr

from app.core.enums import UserRole


class GetUser(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    phone: str | None = None
    address: str | None = None
    laundry_id: int | None = None
    laundry_branch_id: int | None = None



class UpdateUser(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None