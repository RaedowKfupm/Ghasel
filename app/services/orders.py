from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.models.Orders import Orders
from app.models.Users import User
from app.schemas.laundry import Pagination


def get_customer_order(order_id: int, customer: User, db: Session) -> Orders:
    order = (
        db.query(Orders)
        .filter(
            Orders.id == order_id,
            Orders.customer_id == customer.id,
            Orders.is_deleted.is_(False),
        )
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def list_customer_orders(
    pagination: Pagination,
    customer: User,
    db: Session,
) -> list[Orders]:
    return (
        db.query(Orders)
        .filter(
            Orders.customer_id == customer.id,
            Orders.is_deleted.is_(False),
        )
        .order_by(Orders.created_at.desc())
        .offset((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
        .all()
    )


def set_manager_order_status(order: Orders, new_status: OrderStatus, db: Session) -> None:
    order.status = new_status
    if new_status == OrderStatus.ACCEPTED:
        order.accepted_at = datetime.utcnow()
    if new_status == OrderStatus.COMPLETED:
        order.completed_at = datetime.utcnow()
    db.commit()
