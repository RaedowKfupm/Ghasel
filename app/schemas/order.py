from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.enums import OrderStatus

OrderDetails = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=1000)]


class OrderCreate(BaseModel):
    # Omit to publish the order on the marketplace; set to request a specific branch.
    branch_id: int | None = Field(default=None, gt=0)
    details: OrderDetails


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderBranch(BaseModel):
    id: int
    branch_name: str | None = None
    branch_address: str
    phone: str
    laundry_name: str

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    branch_id: int | None = None
    branch: OrderBranch | None = None
    details: str
    status: OrderStatus
    created_at: datetime
    accepted_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
