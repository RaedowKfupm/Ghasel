"""The order state machine: which status changes exist and who may make them.

This module is pure business rules with no database access, so the allowed
transitions are defined in exactly one place and are easy to test and read.
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

TRANSITIONS: dict[tuple[OrderStatus, OrderStatus], Transition] = {
    (t.source, t.target): t
    for t in (
        Transition(OrderStatus.PENDING, OrderStatus.ACCEPTED, _BRANCH, "accepted_at"),
        Transition(OrderStatus.PENDING, OrderStatus.CANCELLED, _CUSTOMER, "cancelled_at"),
        Transition(OrderStatus.ACCEPTED, OrderStatus.CANCELLED, _EITHER, "cancelled_at"),
        Transition(OrderStatus.ACCEPTED, OrderStatus.DELIVERING, _BRANCH),
        Transition(OrderStatus.DELIVERING, OrderStatus.COMPLETED, _BRANCH, "completed_at"),
    )
}

# Statuses reached through dedicated actions (accept/cancel) rather than "advance".
ACTION_ONLY_TARGETS = frozenset({OrderStatus.ACCEPTED, OrderStatus.CANCELLED})

TERMINAL_STATUSES = frozenset({OrderStatus.COMPLETED, OrderStatus.CANCELLED})


def get_transition(source: OrderStatus, target: OrderStatus, actor: OrderActor) -> Transition:
    transition = TRANSITIONS.get((source, target))
    if transition is None or actor not in transition.actors:
        raise InvalidTransitionError(
            f"Cannot move an order from {source.value} to {target.value}"
        )
    return transition


def next_progress_status(source: OrderStatus) -> OrderStatus | None:
    """The status a branch advances an order to next, if any."""
    for (current, target), transition in TRANSITIONS.items():
        if current == source and target not in ACTION_ONLY_TARGETS and OrderActor.BRANCH in transition.actors:
            return target
    return None
