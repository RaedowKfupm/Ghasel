from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.core.enums import LaundryRequestStatus


class LaundryCreate(BaseModel):
	company_name: str


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


class BranchCreate(BaseModel):
	branch_name: str
	branch_address: str
	phone: str


class ManagerCreate(BaseModel):
	name: str
	email: EmailStr
	password: str
	branch_id: int


class ManagerResponse(BaseModel):
	id: int
	name: str
	email: EmailStr
	laundry_branch_id: int

	model_config = ConfigDict(from_attributes=True)


class BranchResponse(BaseModel):
	id: int
	laundry_id: int
	branch_name: str | None = None
	branch_address: str
	operators: list[ManagerResponse] = Field(default_factory=list)
	phone: str
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)
