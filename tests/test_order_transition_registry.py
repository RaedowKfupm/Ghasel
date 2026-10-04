from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.core.enums import OrderStatus, UserRole
from app.db.base import Base
from app.models.Orders import Orders
from app.models.Users import User
from app.services.orders import (
    ORDER_TRANSITIONS,
    dispatch_order_status_transition,
    handle_open_to_accepted,
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def add_order(session: Session, status: OrderStatus, branch_id: int | None) -> Orders:
    order = Orders(
        customer_id=1,
        branch_id=branch_id,
        details="Transition test",
        status=status,
        created_at=datetime.utcnow(),
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def manager(branch_id: int = 10) -> User:
    return User(
        id=100,
        name="Branch operator",
        email="operator@example.com",
        password_hash="unused",
        role=UserRole.MANAGER,
        laundry_branch_id=branch_id,
    )


def test_registry_contains_only_valid_edges():
    assert set(ORDER_TRANSITIONS) == {
        (OrderStatus.OPEN, OrderStatus.ACCEPTED),
        (OrderStatus.PENDING, OrderStatus.ACCEPTED),
        (OrderStatus.ACCEPTED, OrderStatus.DELIVERING),
        (OrderStatus.DELIVERING, OrderStatus.COMPLETED),
    }


def test_open_order_is_claimed_by_manager_branch(db_session: Session):
    order = add_order(db_session, OrderStatus.OPEN, None)

    dispatch_order_status_transition(order.id, OrderStatus.ACCEPTED, manager(10), db_session)

    db_session.refresh(order)
    assert order.status == OrderStatus.ACCEPTED
    assert order.branch_id == 10
    assert order.accepted_at is not None


def test_direct_pending_order_is_accepted_without_reassignment(db_session: Session):
    order = add_order(db_session, OrderStatus.PENDING, 10)

    dispatch_order_status_transition(order.id, OrderStatus.ACCEPTED, manager(10), db_session)

    db_session.refresh(order)
    assert order.status == OrderStatus.ACCEPTED
    assert order.branch_id == 10
    assert order.accepted_at is not None


def test_assigned_order_progression(db_session: Session):
    order = add_order(db_session, OrderStatus.ACCEPTED, 10)

    dispatch_order_status_transition(order.id, OrderStatus.DELIVERING, manager(10), db_session)
    dispatch_order_status_transition(order.id, OrderStatus.COMPLETED, manager(10), db_session)

    db_session.refresh(order)
    assert order.status == OrderStatus.COMPLETED
    assert order.completed_at is not None


def test_unregistered_transition_is_bad_request(db_session: Session):
    order = add_order(db_session, OrderStatus.OPEN, None)

    with pytest.raises(HTTPException) as error:
        dispatch_order_status_transition(order.id, OrderStatus.DELIVERING, manager(10), db_session)

    assert error.value.status_code == 400


def test_manager_cannot_transition_another_branch_order(db_session: Session):
    order = add_order(db_session, OrderStatus.PENDING, 20)

    with pytest.raises(HTTPException) as error:
        dispatch_order_status_transition(order.id, OrderStatus.ACCEPTED, manager(10), db_session)

    assert error.value.status_code == 404


def test_stale_open_claim_fails_compare_and_set(db_session: Session):
    order = add_order(db_session, OrderStatus.OPEN, None)

    handle_open_to_accepted(order.id, 10, db_session)
    with pytest.raises(HTTPException) as error:
        handle_open_to_accepted(order.id, 20, db_session)

    assert error.value.status_code == 409
