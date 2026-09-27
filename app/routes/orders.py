from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
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
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    pass


@router.get("/{order_id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
def get_order(order_id: int, db: Session = Depends(get_db)):
    pass


@router.get("/", response_model=list[OrderResponse], status_code=status.HTTP_200_OK)
def list_orders(
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
):
    pass


@router.patch("/{order_id}/status", status_code=status.HTTP_204_NO_CONTENT)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    return None
