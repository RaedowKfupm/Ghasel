from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import OrderStatus


class OrderCreate(BaseModel):
	branch_id: int | None = Field(default=None, gt=0)
	details: str


class OrderStatusUpdate(BaseModel):
	status: OrderStatus


class OrderResponse(BaseModel):
	id: int
	customer_id: int
	branch_id: int | None = None
	details: str
	status: OrderStatus
	created_at: datetime
	accepted_at: datetime | None = None
	completed_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
