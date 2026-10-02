from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.models.LaundryProfiles import LaundryBranch
from app.models.Orders import Orders
from app.models.Users import User
from app.schemas.laundry import Pagination
from app.schemas.order import OrderCreate


def get_customer_order(order_id: int, customer: User, db: Session) -> Orders:
    order = (
        db.query(Orders)
        .filter(
            Orders.id == order_id,
            Orders.customer_id == customer.id,
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
        )
        .order_by(Orders.created_at.desc())
        .offset((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
        .all()
    )


def create_customer_order(order_data: OrderCreate, customer: User, db: Session) -> Orders:
    branch_exists = db.query(LaundryBranch.id).filter(LaundryBranch.id == order_data.branch_id).first()
    if branch_exists is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    order = Orders(
        customer_id=customer.id,
        branch_id=order_data.branch_id,
        details=order_data.details,
        status=OrderStatus.PENDING,
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def set_manager_order_status(order: Orders, new_status: OrderStatus, db: Session) -> None:
    allowed_next_status = {
        OrderStatus.PENDING: OrderStatus.ACCEPTED,
        OrderStatus.ACCEPTED: OrderStatus.DELIVERING,
        OrderStatus.DELIVERING: OrderStatus.COMPLETED,
    }
    if allowed_next_status.get(order.status) != new_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot change order from {order.status.value} to {new_status.value}",
        )

    previous_status = order.status
    updates = {"status": new_status}
    if new_status == OrderStatus.ACCEPTED:
        updates["accepted_at"] = datetime.utcnow()
    elif new_status == OrderStatus.COMPLETED:
        updates["completed_at"] = datetime.utcnow()

    changed = (
        db.query(Orders)
        .filter(Orders.id == order.id, Orders.status == previous_status)
        .update(updates, synchronize_session=False)
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order status changed concurrently; reload the order and try again",
        )
    db.commit()
