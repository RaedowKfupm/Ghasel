"""Concurrent acceptance must never let two branches win the same order.

These tests use separate database sessions on separate threads, so each request
runs in its own PostgreSQL transaction exactly as concurrent API calls would.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select, text

from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.Orders import OrderStatusEvent, Orders
from app.models.Users import User
from app.services.orders import accept_order
from tests.factories import make_branch, make_manager, make_order, make_user

CONTENDERS = 12


def _attempt_accept(session_factory, manager_id: int, order_id: int, barrier: threading.Barrier) -> int | None:
    """Return the winning branch id, or None if this attempt lost the race.

    A loser either fails the compare-and-set (409) or, if it only reads the order
    after the winner committed, no longer sees it at all (404).
    """
    with session_factory() as session:
        manager = session.get(User, manager_id)
        barrier.wait()
        try:
            return accept_order(order_id, manager, session).branch_id
        except (ConflictError, NotFoundError):
            return None


def test_exactly_one_of_many_simultaneous_acceptances_succeeds(db, session_factory):
    customer = make_user(db)
    managers = [make_manager(db, make_branch(db)) for _ in range(CONTENDERS)]

    for _ in range(5):  # repeat to give interleavings a chance to vary
        order = make_order(db, customer)
        barrier = threading.Barrier(CONTENDERS)
        with ThreadPoolExecutor(max_workers=CONTENDERS) as pool:
            results = list(
                pool.map(lambda m: _attempt_accept(session_factory, m.id, order.id, barrier), managers)
            )

        winners = [branch_id for branch_id in results if branch_id is not None]
        assert len(winners) == 1, results

        db.expire_all()
        stored = db.get(Orders, order.id)
        assert stored.status == OrderStatus.ACCEPTED
        assert stored.branch_id == winners[0]
        accepted_events = db.scalars(
            select(OrderStatusEvent).where(
                OrderStatusEvent.order_id == order.id, OrderStatusEvent.status == OrderStatus.ACCEPTED
            )
        ).all()
        assert len(accepted_events) == 1


def test_acceptance_blocked_by_in_flight_claim_fails_after_it_commits(db, session_factory):
    """Deterministic interleaving: B reads the order as PENDING, then A's claim commits first."""
    customer = make_user(db)
    branch_a, branch_b = make_branch(db), make_branch(db)
    manager_b = make_manager(db, branch_b)
    order = make_order(db, customer)

    with session_factory() as competitor:
        # A locks the row and claims it but has not committed yet.
        competitor.execute(select(Orders).where(Orders.id == order.id).with_for_update())
        competitor.execute(
            text("UPDATE orders SET status = 'ACCEPTED', branch_id = :branch WHERE id = :id"),
            {"branch": branch_a.id, "id": order.id},
        )

        outcome: dict = {}

        def accept_as_b():
            with session_factory() as session:
                try:
                    accept_order(order.id, session.get(User, manager_b.id), session)
                    outcome["result"] = "accepted"
                except ConflictError:
                    outcome["result"] = "conflict"

        worker = threading.Thread(target=accept_as_b)
        worker.start()
        worker.join(timeout=1)
        assert worker.is_alive(), "B should be blocked on A's row lock"

        competitor.commit()
        worker.join(timeout=10)

    assert outcome["result"] == "conflict"
    db.expire_all()
    assert db.get(Orders, order.id).branch_id == branch_a.id
