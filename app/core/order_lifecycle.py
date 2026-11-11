"""The order state machine: which status changes exist and who may make them.

Pure business rules with no database access, so the lifecycle is defined in
exactly one place and is easy to read and test.

    PENDING ──accept──▶ ACCEPTED ─▶ PICKED_UP ─▶ CLEANING ─▶ READY ─▶ DELIVERING ─▶ COMPLETED
       │                   │
       └─cancel (customer) └─cancel (customer or branch, before pickup)
"""

from dataclasses import dataclass
from enum import Enum

from app.core.enums import OrderStatus
from app.core.exceptions import DomainError


class OrderActor(str, Enum):
    CUSTOMER = "customer"
    BRANCH = "branch"


@dataclass(frozen=True)
class Transition:
    source: OrderStatus
    target: OrderStatus
    actors: frozenset[OrderActor]
    timestamp_field: str | None = None


class InvalidTransitionError(DomainError):
    """The requested status change is not part of the lifecycle for this actor."""


_CUSTOMER = frozenset({OrderActor.CUSTOMER})
_BRANCH = frozenset({OrderActor.BRANCH})
_EITHER = _CUSTOMER | _BRANCH

# The branch's working sequence once it has accepted an order.
PROGRESSION: tuple[OrderStatus, ...] = (
    OrderStatus.ACCEPTED,
    OrderStatus.PICKED_UP,
    OrderStatus.CLEANING,
    OrderStatus.READY,
    OrderStatus.DELIVERING,
    OrderStatus.COMPLETED,
)

TRANSITIONS: dict[tuple[OrderStatus, OrderStatus], Transition] = {
    (t.source, t.target): t
    for t in (
        Transition(OrderStatus.PENDING, OrderStatus.ACCEPTED, _BRANCH, "accepted_at"),
        Transition(OrderStatus.PENDING, OrderStatus.CANCELLED, _CUSTOMER, "cancelled_at"),
        # Once the laundry has been collected it is physically with the branch: no cancelling.
        Transition(OrderStatus.ACCEPTED, OrderStatus.CANCELLED, _EITHER, "cancelled_at"),
        *(
            Transition(source, target, _BRANCH, "completed_at" if target == OrderStatus.COMPLETED else None)
            for source, target in zip(PROGRESSION, PROGRESSION[1:])
        ),
    )
}

# Statuses reached through dedicated actions (accept/cancel) rather than "advance".
ACTION_ONLY_TARGETS = frozenset({OrderStatus.ACCEPTED, OrderStatus.CANCELLED})

TERMINAL_STATUSES = frozenset({OrderStatus.COMPLETED, OrderStatus.CANCELLED})


def get_transition(source: OrderStatus, target: OrderStatus, actor: OrderActor) -> Transition:
    transition = TRANSITIONS.get((source, target))
    if transition is None or actor not in transition.actors:
        raise InvalidTransitionError(f"Cannot move an order from {source.value} to {target.value}")
    return transition


def next_progress_status(source: OrderStatus) -> OrderStatus | None:
    """The status the assigned branch advances an order to next, if any."""
    if source not in PROGRESSION or source == PROGRESSION[-1]:
        return None
    return PROGRESSION[PROGRESSION.index(source) + 1]


def can_cancel(status: OrderStatus, actor: OrderActor) -> bool:
    transition = TRANSITIONS.get((status, OrderStatus.CANCELLED))
    return transition is not None and actor in transition.actors
