from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

from app.core.enums import OrderStatus, UserRole
from app.core.order_lifecycle import next_progress_status
from app.schemas.geo import Latitude, Longitude

OrderDetails = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=1000)]
Address = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=300)]


class OrderCreate(BaseModel):
    # Omit to publish the order on the marketplace; set to request a specific branch.
    branch_id: int | None = Field(default=None, gt=0)
    details: OrderDetails
    pickup_address: Address
    pickup_latitude: Latitude
    pickup_longitude: Longitude


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
    pickup_address: str | None = None
    pickup_latitude: float | None = None
    pickup_longitude: float | None = None
    status: OrderStatus
    created_at: datetime
    accepted_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def next_status(self) -> OrderStatus | None:
        """The next working stage the assigned branch can move this order to."""
        return next_progress_status(self.status)


class StatusEventResponse(BaseModel):
    status: OrderStatus
    created_at: datetime
    actor_role: UserRole | None = None

    model_config = ConfigDict(from_attributes=True)


class OrderDetailResponse(OrderResponse):
    history: list[StatusEventResponse] = Field(validation_alias="events")


class AvailableOrderResponse(OrderResponse):
    # Distance from the viewing branch to the pickup point; None if either lacks a location.
    distance_km: float | None = None
