from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Pagination(BaseModel):
	limit: int = Field(default=10, ge=1, le=100)
	page: int = Field(default=1, ge=1)


class LaundryCreate(BaseModel):
	pass


class LaundryResponse(BaseModel):
	id: int
	owner_id: int
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)


class BranchCreate(BaseModel):
	branch_name: str
	branch_address: str
	manager_id: int
	phone: str


class BranchResponse(BaseModel):
	id: int
	laundry_id: int
	branch_name: str | None = None
	branch_address: str
	manager_id: int
	phone: str
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)
