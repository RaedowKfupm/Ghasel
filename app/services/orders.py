from datetime import datetime
from collections.abc import Callable

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.enums import OrderStatus, UserRole
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


def list_orders_for_user(
    pagination: Pagination,
    user: User,
    db: Session,
) -> list[Orders]:
    query = db.query(Orders)
    if user.role == UserRole.CUSTOMER:
        query = query.filter(Orders.customer_id == user.id)
    elif user.role == UserRole.MANAGER:
        if user.laundry_branch_id is None:
            raise HTTPException(status_code=403, detail="No branch is assigned to this manager")
        query = query.filter(
            or_(
                and_(Orders.status == OrderStatus.OPEN, Orders.branch_id.is_(None)),
                Orders.branch_id == user.laundry_branch_id,
            )
        )
    elif user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return (
        query.order_by(Orders.created_at.desc())
        .offset((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
        .all()
    )


def create_customer_order(order_data: OrderCreate, customer: User, db: Session) -> Orders:
    initial_status = OrderStatus.OPEN
    if order_data.branch_id is not None:
        branch_exists = (
            db.query(LaundryBranch.id)
            .filter(LaundryBranch.id == order_data.branch_id)
            .first()
        )
        if branch_exists is None:
            raise HTTPException(status_code=404, detail="Branch not found")
        initial_status = OrderStatus.PENDING

    order = Orders(
        customer_id=customer.id,
        branch_id=order_data.branch_id,
        details=order_data.details,
        status=initial_status,
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def dispatch_order_status_transition(
    order_id: int,
    new_status: OrderStatus,
    manager: User,
    db: Session,
) -> None:
    branch_id = manager.laundry_branch_id
    if branch_id is None:
        raise HTTPException(status_code=403, detail="No branch is assigned to this manager")

    order = (
        db.query(Orders.status, Orders.branch_id)
        .filter(Orders.id == order_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.branch_id is not None and order.branch_id != branch_id:
        raise HTTPException(status_code=404, detail="Order not found")

    handler = ORDER_TRANSITIONS.get((order.status, new_status))
    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transition from {order.status.value} to {new_status.value} is not allowed",
        )
    handler(order_id, branch_id, db)


def _apply_order_transition(
    order_id: int,
    branch_id: int,
    current_status: OrderStatus,
    target_status: OrderStatus,
    db: Session,
    *,
    assign_branch: bool = False,
    timestamp_field: str | None = None,
) -> None:
    conditions = [Orders.id == order_id, Orders.status == current_status]
    values = {"status": target_status}
    if assign_branch:
        conditions.append(Orders.branch_id.is_(None))
        values["branch_id"] = branch_id
    else:
        conditions.append(Orders.branch_id == branch_id)
    if timestamp_field is not None:
        values[timestamp_field] = datetime.utcnow()

    changed = (
        db.query(Orders)
        .filter(*conditions)
        .update(values, synchronize_session=False)
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order status changed concurrently; reload the order and try again",
        )
    db.commit()


def handle_open_to_accepted(order_id: int, branch_id: int, db: Session) -> None:
    _apply_order_transition(
        order_id,
        branch_id,
        OrderStatus.OPEN,
        OrderStatus.ACCEPTED,
        db,
        assign_branch=True,
        timestamp_field="accepted_at",
    )


def handle_pending_to_accepted(order_id: int, branch_id: int, db: Session) -> None:
    _apply_order_transition(
        order_id,
        branch_id,
        OrderStatus.PENDING,
        OrderStatus.ACCEPTED,
        db,
        timestamp_field="accepted_at",
    )
    # TODO: enqueue assigned-order notifications after the transaction commits.


def handle_accepted_to_delivering(order_id: int, branch_id: int, db: Session) -> None:
    _apply_order_transition(
        order_id,
        branch_id,
        OrderStatus.ACCEPTED,
        OrderStatus.DELIVERING,
        db,
    )


def handle_delivering_to_completed(order_id: int, branch_id: int, db: Session) -> None:
    _apply_order_transition(
        order_id,
        branch_id,
        OrderStatus.DELIVERING,
        OrderStatus.COMPLETED,
        db,
        timestamp_field="completed_at",
    )


OrderTransitionHandler = Callable[[int, int, Session], None]
ORDER_TRANSITIONS: dict[tuple[OrderStatus, OrderStatus], OrderTransitionHandler] = {
    (OrderStatus.OPEN, OrderStatus.ACCEPTED): handle_open_to_accepted,
    (OrderStatus.PENDING, OrderStatus.ACCEPTED): handle_pending_to_accepted,
    (OrderStatus.ACCEPTED, OrderStatus.DELIVERING): handle_accepted_to_delivering,
    (OrderStatus.DELIVERING, OrderStatus.COMPLETED): handle_delivering_to_completed,
}
