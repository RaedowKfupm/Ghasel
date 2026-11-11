"""The lifecycle table itself: every edge is intended and roles are respected."""

import pytest

from app.core.enums import OrderStatus as S
from app.core.order_lifecycle import (
    TRANSITIONS,
    InvalidTransitionError,
    OrderActor,
    can_cancel,
    get_transition,
)

EXPECTED_EDGES = {
    (S.PENDING, S.ACCEPTED): {OrderActor.BRANCH},
    (S.PENDING, S.CANCELLED): {OrderActor.CUSTOMER},
    (S.ACCEPTED, S.CANCELLED): {OrderActor.CUSTOMER, OrderActor.BRANCH},
    (S.ACCEPTED, S.PICKED_UP): {OrderActor.BRANCH},
    (S.PICKED_UP, S.CLEANING): {OrderActor.BRANCH},
    (S.CLEANING, S.READY): {OrderActor.BRANCH},
    (S.READY, S.DELIVERING): {OrderActor.BRANCH},
    (S.DELIVERING, S.COMPLETED): {OrderActor.BRANCH},
}


def test_lifecycle_has_exactly_the_intended_edges():
    assert {edge: set(t.actors) for edge, t in TRANSITIONS.items()} == EXPECTED_EDGES


@pytest.mark.parametrize("terminal", [S.COMPLETED, S.CANCELLED])
def test_terminal_states_have_no_exits(terminal):
    assert not [edge for edge in TRANSITIONS if edge[0] == terminal]


def test_customer_cannot_progress_an_order():
    with pytest.raises(InvalidTransitionError):
        get_transition(S.ACCEPTED, S.PICKED_UP, OrderActor.CUSTOMER)


def test_branch_cannot_cancel_before_accepting():
    assert not can_cancel(S.PENDING, OrderActor.BRANCH)
    assert can_cancel(S.PENDING, OrderActor.CUSTOMER)


def test_milestone_timestamps():
    assert get_transition(S.PENDING, S.ACCEPTED, OrderActor.BRANCH).timestamp_field == "accepted_at"
    assert get_transition(S.DELIVERING, S.COMPLETED, OrderActor.BRANCH).timestamp_field == "completed_at"
    assert get_transition(S.PENDING, S.CANCELLED, OrderActor.CUSTOMER).timestamp_field == "cancelled_at"
