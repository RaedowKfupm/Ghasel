from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import Database, Page, require_roles
from app.core.enums import UserRole
from app.models.Users import User
from app.schemas.order import AvailableOrderResponse, OrderCreate, OrderResponse, OrderStatusUpdate
from app.services import orders as order_service

router = APIRouter(prefix="/orders", tags=["Orders"])

Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]
Manager = Annotated[User, Depends(require_roles(UserRole.MANAGER))]
OrderParticipant = Annotated[User, Depends(require_roles(UserRole.CUSTOMER, UserRole.MANAGER))]
OrderViewer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER, UserRole.MANAGER, UserRole.ADMIN))]


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, customer: Customer, db: Database):
    return order_service.create_order(order_data, customer, db)


@router.get("/", response_model=list[OrderResponse])
def list_orders(pagination: Page, user: OrderViewer, db: Database):
    return order_service.list_orders(pagination, user, db)


@router.get("/available", response_model=list[AvailableOrderResponse])
def list_available_orders(pagination: Page, manager: Manager, db: Database):
    return order_service.list_available_orders(pagination, manager, db)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, user: OrderViewer, db: Database):
    return order_service.get_order(order_id, user, db)


@router.post("/{order_id}/accept", response_model=OrderResponse)
def accept_order(order_id: int, manager: Manager, db: Database):
    return order_service.accept_order(order_id, manager, db)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: int, user: OrderParticipant, db: Database):
    return order_service.cancel_order(order_id, user, db)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def advance_order_status(order_id: int, status_data: OrderStatusUpdate, manager: Manager, db: Database):
    return order_service.advance_order_status(order_id, status_data.status, manager, db)
