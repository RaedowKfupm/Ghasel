"""Order use cases: creation, visibility, marketplace acceptance and status changes.

Every status change is a single conditional ``UPDATE ... WHERE status = <expected>``.
PostgreSQL row locking serialises concurrent updates to the same row and re-checks
the WHERE clause after the first writer commits, so only one of several racing
requests can succeed; the others match zero rows and receive 409 Conflict.
"""

from sqlalchemy import Float, Select, or_, select, update
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import ColumnElement, func

from app.core.enums import OrderStatus, UserRole
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.db.spatial import METRES_PER_KM
from app.models.LaundryProfiles import LaundryBranch
from app.models.Orders import Orders
from app.models.Users import User
from app.schemas.order import AvailableOrderResponse, OrderCreate
from app.schemas.pagination import Pagination
from app.services.order_lifecycle import (
    ACTION_ONLY_TARGETS,
    InvalidTransitionError,
    OrderActor,
    Transition,
    get_transition,
)

_ORDER_NOT_FOUND = "Order not found"


# --- Queries -----------------------------------------------------------------


def _order_query() -> Select:
    return select(Orders).options(selectinload(Orders.branch).selectinload(LaundryBranch.laundry))


def _paginate(query: Select, pagination: Pagination) -> Select:
    return query.order_by(Orders.created_at.desc(), Orders.id.desc()).offset(pagination.offset).limit(pagination.limit)


def _manager_branch_id(manager: User) -> int:
    if manager.laundry_branch_id is None:
        raise PermissionDeniedError("No branch is assigned to this manager")
    return manager.laundry_branch_id


def _branch_location(branch_id: int) -> ColumnElement:
    return select(LaundryBranch.location).where(LaundryBranch.id == branch_id).scalar_subquery()


def _within_service_area(branch_id: int) -> ColumnElement[bool]:
    """The order's pickup point lies inside the branch's service radius (PostGIS, metres)."""
    service_radius_km = (
        select(LaundryBranch.service_radius_km).where(LaundryBranch.id == branch_id).scalar_subquery()
    )
    return func.ST_DWithin(Orders.pickup_location, _branch_location(branch_id), service_radius_km * METRES_PER_KM)


def _available_to_branch(branch_id: int) -> ColumnElement[bool]:
    """Pending orders a branch may accept: direct requests to it, and nearby marketplace orders.

    Branches without a location see no marketplace orders (ST_DWithin with NULL is not true).
    """
    return (Orders.status == OrderStatus.PENDING) & or_(
        Orders.branch_id == branch_id,
        Orders.branch_id.is_(None) & _within_service_area(branch_id),
    )


def _visible_to(user: User) -> ColumnElement[bool] | None:
    """SQL condition restricting orders to those ``user`` may see (None = unrestricted)."""
    if user.role == UserRole.ADMIN:
        return None
    if user.role == UserRole.CUSTOMER:
        return Orders.customer_id == user.id
    if user.role == UserRole.MANAGER:
        branch_id = _manager_branch_id(user)
        return or_(Orders.branch_id == branch_id, _available_to_branch(branch_id))
    raise PermissionDeniedError("Insufficient permissions")


def list_orders(pagination: Pagination, user: User, db: Session) -> list[Orders]:
    """Customers see their orders, managers their branch's orders, admins everything."""
    query = _order_query()
    if user.role == UserRole.CUSTOMER:
        query = query.where(Orders.customer_id == user.id)
    elif user.role == UserRole.MANAGER:
        query = query.where(Orders.branch_id == _manager_branch_id(user))
    elif user.role != UserRole.ADMIN:
        raise PermissionDeniedError("Insufficient permissions")
    return list(db.scalars(_paginate(query, pagination)))


def list_available_orders(pagination: Pagination, manager: User, db: Session) -> list[AvailableOrderResponse]:
    """Orders the manager's branch may accept, nearest pickup first."""
    branch_id = _manager_branch_id(manager)
    distance_m = func.ST_Distance(Orders.pickup_location, _branch_location(branch_id), type_=Float)
    rows = db.execute(
        _order_query()
        .add_columns(distance_m.label("distance_m"))
        .where(_available_to_branch(branch_id))
        .order_by(distance_m.asc().nulls_last(), Orders.created_at.desc(), Orders.id.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    ).all()
    return [
        AvailableOrderResponse.model_validate(order).model_copy(
            update={"distance_km": None if distance is None else round(distance / METRES_PER_KM, 3)}
        )
        for order, distance in rows
    ]


def get_order(order_id: int, user: User, db: Session) -> Orders:
    query = _order_query().where(Orders.id == order_id)
    visibility = _visible_to(user)
    if visibility is not None:
        query = query.where(visibility)
    order = db.scalar(query)
    if order is None:
        raise NotFoundError(_ORDER_NOT_FOUND)
    return order


# --- Commands ----------------------------------------------------------------


def create_order(order_data: OrderCreate, customer: User, db: Session) -> Orders:
    if order_data.branch_id is not None and db.get(LaundryBranch, order_data.branch_id) is None:
        raise NotFoundError("Branch not found")

    order = Orders(customer_id=customer.id, status=OrderStatus.PENDING, **order_data.model_dump())
    db.add(order)
    db.commit()
    return get_order(order.id, customer, db)


def _apply_transition(
    order: Orders,
    transition: Transition,
    db: Session,
    *,
    guards: tuple[ColumnElement[bool], ...] = (),
    values: dict | None = None,
) -> None:
    """Compare-and-set the order's status; fails if anyone changed it first."""
    changes = {"status": transition.target, **(values or {})}
    if transition.timestamp_field:
        changes[transition.timestamp_field] = func.now()

    updated = db.execute(
        update(Orders)
        .where(Orders.id == order.id, Orders.status == transition.source, *guards)
        .values(**changes)
        .returning(Orders.id)
    ).first()
    if updated is None:
        db.rollback()
        raise ConflictError("This order was just updated by someone else; reload and try again")
    db.commit()


def accept_order(order_id: int, manager: User, db: Session) -> Orders:
    branch_id = _manager_branch_id(manager)
    order = get_order(order_id, manager, db)
    if order.status != OrderStatus.PENDING:
        raise ConflictError("This order is no longer available")

    transition = get_transition(order.status, OrderStatus.ACCEPTED, OrderActor.BRANCH)
    _apply_transition(
        order,
        transition,
        db,
        # Re-checked inside the UPDATE so a concurrent acceptance cannot also succeed.
        guards=(_available_to_branch(branch_id),),
        values={"branch_id": branch_id},
    )
    return get_order(order_id, manager, db)


def cancel_order(order_id: int, user: User, db: Session) -> Orders:
    order = get_order(order_id, user, db)
    if user.role == UserRole.CUSTOMER:
        actor, guard = OrderActor.CUSTOMER, Orders.customer_id == user.id
    elif user.role == UserRole.MANAGER:
        actor, guard = OrderActor.BRANCH, Orders.branch_id == _manager_branch_id(user)
        if order.branch_id is None:
            raise NotFoundError(_ORDER_NOT_FOUND)
    else:
        raise PermissionDeniedError("Insufficient permissions")

    transition = get_transition(order.status, OrderStatus.CANCELLED, actor)
    _apply_transition(order, transition, db, guards=(guard,))
    return get_order(order_id, user, db)


def advance_order_status(order_id: int, target: OrderStatus, manager: User, db: Session) -> Orders:
    """Move an order the branch already owns to its next working status."""
    if target in ACTION_ONLY_TARGETS:
        raise InvalidTransitionError(f"Use the dedicated endpoint to mark an order {target.value}")

    branch_id = _manager_branch_id(manager)
    order = get_order(order_id, manager, db)
    if order.branch_id != branch_id:
        raise NotFoundError(_ORDER_NOT_FOUND)

    transition = get_transition(order.status, target, OrderActor.BRANCH)
    _apply_transition(order, transition, db, guards=(Orders.branch_id == branch_id,))
    return get_order(order_id, manager, db)
