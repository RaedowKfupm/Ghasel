from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.Users import User
from app.services.orders import (
    create_customer_order,
    dispatch_order_status_transition,
    get_customer_order,
    list_orders_for_user,
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
    user: User = Depends(
        require_roles(UserRole.CUSTOMER, UserRole.MANAGER, UserRole.ADMIN)
    ),
):
    return list_orders_for_user(pagination, user, db)

#laundryManager
@router.patch("/{order_id}/status", status_code=status.HTTP_204_NO_CONTENT)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.MANAGER)),
):
    dispatch_order_status_transition(order_id, status_data.status, user, db)
