from pydantic import BaseModel, EmailStr

from app.core.enums import UserRole
from app.schemas.fields import Address, PersonName, Phone


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
    name: PersonName | None = None
    email: EmailStr | None = None
    phone: Phone | None = None
    address: Address | None = None
