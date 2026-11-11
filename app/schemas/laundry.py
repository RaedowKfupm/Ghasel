from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.enums import LaundryRequestStatus
from app.schemas.fields import Password, PersonName

CompanyName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]


class LaundryCreate(BaseModel):
    company_name: CompanyName


class LaundryRequestResponse(BaseModel):
    id: int
    owner_id: int
    company_name: str
    status: LaundryRequestStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LaundryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManagerCreate(BaseModel):
    name: PersonName
    email: EmailStr
    password: Password
    branch_id: int = Field(gt=0)


class ManagerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    laundry_branch_id: int

    model_config = ConfigDict(from_attributes=True)
