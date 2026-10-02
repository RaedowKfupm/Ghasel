from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import ManagerOrder, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.Users import User
from app.services.orders import (
    create_customer_order,
    get_customer_order,
    list_customer_orders,
    set_manager_order_status,
)
from app.schemas.laundry import Pagination
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
#user
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.CUSTOMER)),
):
    return create_customer_order(order_data, user, db)


@router.get("/{order_id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.CUSTOMER)),
):
    return get_customer_order(order_id, user, db)


@router.get("/", response_model=list[OrderResponse], status_code=status.HTTP_200_OK)
def list_orders(
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.CUSTOMER)),
):
    return list_customer_orders(pagination, user, db)

#laundryManager
@router.patch("/{order_id}/status", status_code=status.HTTP_204_NO_CONTENT)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    order: ManagerOrder,
    db: Session = Depends(get_db),
):
    set_manager_order_status(order, status_data.status, db)
