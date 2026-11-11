from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.enums import LaundryRequestStatus

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
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    branch_id: int = Field(gt=0)


class ManagerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    laundry_branch_id: int

    model_config = ConfigDict(from_attributes=True)
