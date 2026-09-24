from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderCreate(BaseModel):
	branch_id: int
	details: str


class OrderStatusUpdate(BaseModel):
	status: str


class OrderResponse(BaseModel):
	id: int
	customer_id: int
	branch_id: int
	details: str
	status: str
	address: str
	created_at: datetime
	accepted_at: datetime | None = None
	completed_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
