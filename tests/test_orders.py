"""Marketplace ordering: creation, visibility, acceptance, cancellation and progression."""

import pytest
from sqlalchemy import text, update
from sqlalchemy.exc import IntegrityError

from app.core.enums import OrderStatus, UserRole
from app.models.Orders import Orders
from tests.factories import ORIGIN, auth_headers, make_branch, make_manager, make_order, make_user

PICKUP = {"pickup_address": "Building 57, KFUPM", "pickup_latitude": ORIGIN[0], "pickup_longitude": ORIGIN[1]}


def order_payload(**fields) -> dict:
    return {"details": "3 shirts, wash and iron", **PICKUP, **fields}


@pytest.fixture
def customer(db):
    return make_user(db, UserRole.CUSTOMER)


@pytest.fixture
def branch_a(db):
    return make_branch(db, branch_name="Alpha")


@pytest.fixture
def branch_b(db):
    return make_branch(db, branch_name="Beta")


@pytest.fixture
def manager_a(db, branch_a):
    return make_manager(db, branch_a)


@pytest.fixture
def manager_b(db, branch_b):
    return make_manager(db, branch_b)


def ids(response) -> set[int]:
    return {order["id"] for order in response.json()}


class TestCreateOrder:
    def test_order_without_branch_is_pending_and_unassigned(self, client, customer):
        response = client.post("/orders/", headers=auth_headers(customer), json=order_payload(details="2 duvets"))
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "pending"
        assert body["branch_id"] is None
        assert body["customer_id"] == customer.id

    def test_direct_order_targets_existing_branch(self, client, customer, branch_a):
        response = client.post("/orders/", headers=auth_headers(customer), json=order_payload(branch_id=branch_a.id))
        assert response.status_code == 201
        assert response.json()["branch"]["branch_name"] == "Alpha"

    def test_unknown_branch_is_rejected(self, client, customer):
        response = client.post("/orders/", headers=auth_headers(customer), json=order_payload(branch_id=999))
        assert response.status_code == 404

    @pytest.mark.parametrize("details", ["", "  ", "x" * 1001])
    def test_details_are_validated(self, client, customer, details):
        response = client.post("/orders/", headers=auth_headers(customer), json=order_payload(details=details))
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "pickup",
        [
            {"pickup_latitude": 90.5},
            {"pickup_longitude": -181},
            {"pickup_latitude": None},
            {"pickup_address": ""},
        ],
    )
    def test_pickup_location_is_required_and_validated(self, client, customer, pickup):
        response = client.post("/orders/", headers=auth_headers(customer), json=order_payload(**pickup))
        assert response.status_code == 422

    def test_non_finite_coordinates_in_json_body_are_rejected(self, client, customer):
        raw = '{"details": "Shirts", "pickup_address": "Home", "pickup_latitude": NaN, "pickup_longitude": 50}'
        response = client.post(
            "/orders/", headers={**auth_headers(customer), "Content-Type": "application/json"}, content=raw
        )
        assert response.status_code == 422

    def test_pickup_location_is_stored(self, client, customer):
        body = client.post("/orders/", headers=auth_headers(customer), json=order_payload()).json()
        assert (body["pickup_latitude"], body["pickup_longitude"]) == ORIGIN

    def test_only_customers_create_orders(self, client, manager_a):
        response = client.post("/orders/", headers=auth_headers(manager_a), json=order_payload())
        assert response.status_code == 403


class TestVisibility:
    def test_customer_sees_only_own_orders(self, client, db, customer):
        mine = make_order(db, customer)
        other = make_order(db, make_user(db))
        assert ids(client.get("/orders/", headers=auth_headers(customer))) == {mine.id}
        assert client.get(f"/orders/{other.id}", headers=auth_headers(customer)).status_code == 404

    def test_available_feed_has_marketplace_and_own_direct_orders(
        self, client, db, customer, branch_a, branch_b, manager_a
    ):
        marketplace = make_order(db, customer)
        direct_to_a = make_order(db, customer, branch_a)
        direct_to_b = make_order(db, customer, branch_b)
        make_order(db, customer, branch_a, status=OrderStatus.ACCEPTED)

        available = ids(client.get("/orders/available", headers=auth_headers(manager_a)))
        assert available == {marketplace.id, direct_to_a.id}
        assert direct_to_b.id not in available

    def test_manager_cannot_read_another_branchs_order(self, client, db, customer, branch_b, manager_a):
        order = make_order(db, customer, branch_b, status=OrderStatus.ACCEPTED)
        assert client.get(f"/orders/{order.id}", headers=auth_headers(manager_a)).status_code == 404

    def test_manager_without_branch_is_forbidden(self, client, db):
        unassigned = make_user(db, UserRole.MANAGER)
        assert client.get("/orders/available", headers=auth_headers(unassigned)).status_code == 403

    @pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"page": 0}, {"page": "two"}])
    def test_invalid_pagination_is_rejected(self, client, customer, params):
        assert client.get("/orders/", headers=auth_headers(customer), params=params).status_code == 422

    def test_admin_sees_all_orders(self, client, db, customer, branch_a):
        orders = {make_order(db, customer).id, make_order(db, customer, branch_a).id}
        admin = make_user(db, UserRole.ADMIN)
        assert ids(client.get("/orders/", headers=auth_headers(admin))) == orders


class TestAcceptance:
    def test_accepting_assigns_branch_and_timestamps(self, client, db, customer, branch_a, manager_a):
        order = make_order(db, customer)
        response = client.post(f"/orders/{order.id}/accept", headers=auth_headers(manager_a))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "accepted"
        assert body["branch_id"] == branch_a.id
        assert body["accepted_at"] is not None

    def test_second_branch_cannot_accept_taken_order(self, client, db, customer, manager_a, manager_b):
        order = make_order(db, customer)
        client.post(f"/orders/{order.id}/accept", headers=auth_headers(manager_a))
        response = client.post(f"/orders/{order.id}/accept", headers=auth_headers(manager_b))
        assert response.status_code in (404, 409)
        db.expire_all()
        assert db.get(Orders, order.id).branch_id == manager_a.laundry_branch_id

    def test_branch_cannot_accept_direct_order_for_another_branch(self, client, db, customer, branch_a, manager_b):
        order = make_order(db, customer, branch_a)
        assert client.post(f"/orders/{order.id}/accept", headers=auth_headers(manager_b)).status_code == 404

    def test_customers_cannot_accept(self, client, db, customer):
        order = make_order(db, customer)
        assert client.post(f"/orders/{order.id}/accept", headers=auth_headers(customer)).status_code == 403

    def test_cancelled_order_cannot_be_accepted(self, client, db, customer, branch_a, manager_a):
        order = make_order(db, customer, branch_a, status=OrderStatus.CANCELLED)
        assert client.post(f"/orders/{order.id}/accept", headers=auth_headers(manager_a)).status_code == 409


class TestCancellation:
    def test_customer_cancels_pending_order(self, client, db, customer):
        order = make_order(db, customer)
        response = client.post(f"/orders/{order.id}/cancel", headers=auth_headers(customer))
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        assert response.json()["cancelled_at"] is not None

    def test_customer_cannot_cancel_someone_elses_order(self, client, db, customer):
        order = make_order(db, make_user(db))
        assert client.post(f"/orders/{order.id}/cancel", headers=auth_headers(customer)).status_code == 404

    def test_assigned_branch_can_cancel_accepted_order(self, client, db, customer, branch_a, manager_a):
        order = make_order(db, customer, branch_a, status=OrderStatus.ACCEPTED)
        assert client.post(f"/orders/{order.id}/cancel", headers=auth_headers(manager_a)).status_code == 200

    def test_branch_cannot_cancel_marketplace_order(self, client, db, customer, manager_a):
        order = make_order(db, customer)
        assert client.post(f"/orders/{order.id}/cancel", headers=auth_headers(manager_a)).status_code == 404

    def test_cannot_cancel_once_out_for_delivery(self, client, db, customer, branch_a):
        order = make_order(db, customer, branch_a, status=OrderStatus.DELIVERING)
        assert client.post(f"/orders/{order.id}/cancel", headers=auth_headers(customer)).status_code == 400


class TestProgression:
    def test_assigned_branch_moves_order_through_lifecycle(self, client, db, customer, branch_a, manager_a):
        order = make_order(db, customer, branch_a, status=OrderStatus.ACCEPTED)
        for target in ("delivering", "completed"):
            response = client.patch(
                f"/orders/{order.id}/status", headers=auth_headers(manager_a), json={"status": target}
            )
            assert response.status_code == 200, response.json()
            assert response.json()["status"] == target
        assert response.json()["completed_at"] is not None

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (OrderStatus.ACCEPTED, "completed"),
            (OrderStatus.COMPLETED, "delivering"),
            (OrderStatus.CANCELLED, "delivering"),
        ],
    )
    def test_skipping_or_reversing_states_is_rejected(self, client, db, customer, branch_a, manager_a, current, target):
        order = make_order(db, customer, branch_a, status=current)
        response = client.patch(f"/orders/{order.id}/status", headers=auth_headers(manager_a), json={"status": target})
        assert response.status_code == 400

    @pytest.mark.parametrize("target", ["accepted", "cancelled"])
    def test_status_endpoint_cannot_bypass_accept_or_cancel(self, client, db, customer, branch_a, manager_a, target):
        order = make_order(db, customer, branch_a)
        response = client.patch(f"/orders/{order.id}/status", headers=auth_headers(manager_a), json={"status": target})
        assert response.status_code == 400

    def test_other_branch_cannot_progress_order(self, client, db, customer, branch_a, manager_b):
        order = make_order(db, customer, branch_a, status=OrderStatus.ACCEPTED)
        response = client.patch(
            f"/orders/{order.id}/status", headers=auth_headers(manager_b), json={"status": "delivering"}
        )
        assert response.status_code == 404

    def test_unknown_status_value_is_rejected(self, client, db, customer, branch_a, manager_a):
        order = make_order(db, customer, branch_a, status=OrderStatus.ACCEPTED)
        response = client.patch(f"/orders/{order.id}/status", headers=auth_headers(manager_a), json={"status": "lost"})
        assert response.status_code == 422


class TestDatabaseConstraints:
    def test_non_pending_order_must_have_a_branch(self, db, customer):
        order = make_order(db, customer)
        with pytest.raises(IntegrityError):
            db.execute(update(Orders).where(Orders.id == order.id).values(status=OrderStatus.ACCEPTED))
            db.commit()
        db.rollback()

    def test_status_must_be_a_known_value(self, db, customer):
        order = make_order(db, customer)
        with pytest.raises(IntegrityError):
            db.execute(text("UPDATE orders SET status = 'LOST' WHERE id = :id"), {"id": order.id})
            db.commit()
        db.rollback()
