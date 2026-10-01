from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.core.enums import OrderStatus


class OrderCreate(BaseModel):
	branch_id: int
	details: str


class OrderStatusUpdate(BaseModel):
	status: OrderStatus


class OrderResponse(BaseModel):
	id: int
	customer_id: int
	branch_id: int
	details: str
	status: OrderStatus
	created_at: datetime
	accepted_at: datetime | None = None
	completed_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
