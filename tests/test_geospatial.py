"""Nearby branch discovery and distance-based marketplace eligibility."""

import math

import pytest
from sqlalchemy import func, select

from app.core.enums import UserRole
from app.db.spatial import point
from app.models.LaundryProfiles import LaundryBranch
from tests.factories import (
    ORIGIN,
    auth_headers,
    make_branch,
    make_laundry,
    make_manager,
    make_order,
    make_user,
    north_of,
)


def search(client, latitude=ORIGIN[0], longitude=ORIGIN[1], **params):
    return client.get("/branches/nearby", params={"latitude": latitude, "longitude": longitude, **params})


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def stored_distance_km(db, branch: LaundryBranch, origin=ORIGIN) -> float:
    metres = db.scalar(
        select(func.ST_Distance(LaundryBranch.location, point(*origin))).where(LaundryBranch.id == branch.id)
    )
    return metres / 1000


class TestNearbySearch:
    def test_results_are_ordered_by_distance_with_distances(self, client, db):
        far = make_branch(db, location=north_of(ORIGIN, 3), branch_name="Far")
        near = make_branch(db, location=north_of(ORIGIN, 1), branch_name="Near")
        middle = make_branch(db, location=north_of(ORIGIN, 2), branch_name="Middle")

        body = search(client, radius_km=5).json()

        assert [b["id"] for b in body] == [near.id, middle.id, far.id]
        distances = [b["distance_km"] for b in body]
        assert distances == sorted(distances)
        for branch, expected_km in zip(body, (1, 2, 3), strict=True):
            assert branch["distance_km"] == pytest.approx(expected_km, rel=0.01)

    def test_distance_matches_independent_great_circle_estimate(self, client, db):
        destination = (26.4207, 50.0888)  # Dammam corniche, ~14 km away
        make_branch(db, location=destination)
        body = search(client, radius_km=20).json()
        assert body[0]["distance_km"] == pytest.approx(haversine_km(ORIGIN, destination), rel=0.005)

    def test_radius_excludes_branches_just_outside(self, client, db):
        inside = make_branch(db, location=north_of(ORIGIN, 4.8))
        make_branch(db, location=north_of(ORIGIN, 5.2))
        assert [b["id"] for b in search(client, radius_km=5).json()] == [inside.id]

    def test_radius_boundary_is_inclusive(self, client, db):
        branch = make_branch(db, location=north_of(ORIGIN, 5))
        exact_km = stored_distance_km(db, branch)

        assert [b["id"] for b in search(client, radius_km=exact_km).json()] == [branch.id]
        assert search(client, radius_km=exact_km - 0.001).json() == []

    def test_branches_without_coordinates_are_not_listed(self, client, db):
        make_branch(db, location=None)
        located = make_branch(db)
        assert [b["id"] for b in search(client).json()] == [located.id]

    def test_pagination_continues_in_distance_order(self, client, db):
        branches = [make_branch(db, location=north_of(ORIGIN, km)) for km in (0.5, 1, 1.5, 2, 2.5)]
        page_two = search(client, radius_km=5, limit=2, page=2).json()
        assert [b["id"] for b in page_two] == [branches[2].id, branches[3].id]

    def test_results_include_laundry_name(self, client, db):
        make_branch(db, laundry=make_laundry(db, name="Crisp & Clean"))
        assert search(client).json()[0]["laundry_name"] == "Crisp & Clean"

    @pytest.mark.parametrize(
        "params",
        [
            {"latitude": 90.0001},
            {"latitude": -91},
            {"longitude": 180.5},
            {"latitude": "nan"},
            {"longitude": "inf"},
            {"latitude": "north"},
            {"radius_km": 0},
            {"radius_km": 51},
        ],
    )
    def test_invalid_search_input_is_rejected(self, client, params):
        assert search(client, **params).status_code == 422

    def test_missing_coordinates_are_rejected(self, client):
        assert client.get("/branches/nearby", params={"latitude": ORIGIN[0]}).status_code == 422


class TestMarketplaceEligibility:
    def test_branch_sees_only_marketplace_orders_inside_its_radius(self, client, db):
        branch = make_branch(db, service_radius_km=5)
        manager = make_manager(db, branch)
        customer = make_user(db)
        nearby = make_order(db, customer, pickup=north_of(ORIGIN, 3))
        distant = make_order(db, customer, pickup=north_of(ORIGIN, 8))

        available = client.get("/orders/available", headers=auth_headers(manager)).json()

        assert [o["id"] for o in available] == [nearby.id]
        assert available[0]["distance_km"] == pytest.approx(3, rel=0.01)
        assert client.post(f"/orders/{distant.id}/accept", headers=auth_headers(manager)).status_code == 404

    def test_enlarging_service_radius_reveals_more_orders(self, client, db):
        branch = make_branch(db, service_radius_km=5)
        manager = make_manager(db, branch)
        order = make_order(db, make_user(db), pickup=north_of(ORIGIN, 8))

        client.patch(f"/branches/{branch.id}", headers=auth_headers(manager), json={"service_radius_km": 10})

        assert client.post(f"/orders/{order.id}/accept", headers=auth_headers(manager)).status_code == 200

    def test_branch_without_location_sees_direct_but_not_marketplace_orders(self, client, db):
        branch = make_branch(db, location=None)
        manager = make_manager(db, branch)
        customer = make_user(db)
        make_order(db, customer)
        direct = make_order(db, customer, branch)

        available = client.get("/orders/available", headers=auth_headers(manager)).json()
        assert [o["id"] for o in available] == [direct.id]

    def test_available_feed_lists_nearest_pickups_first(self, client, db):
        manager = make_manager(db, make_branch(db))
        customer = make_user(db)
        second = make_order(db, customer, pickup=north_of(ORIGIN, 2))
        first = make_order(db, customer, pickup=north_of(ORIGIN, 1))
        available = client.get("/orders/available", headers=auth_headers(manager)).json()
        assert [o["id"] for o in available] == [first.id, second.id]


class TestBranchManagement:
    @pytest.fixture
    def branch(self, db):
        return make_branch(db)

    def test_owner_updates_branch_location(self, client, db, branch):
        owner = make_user(db, UserRole.LAUNDRY, laundry_id=branch.laundry_id)
        response = client.patch(
            f"/branches/{branch.id}", headers=auth_headers(owner), json={"latitude": 24.7136, "longitude": 46.6753}
        )
        assert response.status_code == 200
        assert (response.json()["latitude"], response.json()["longitude"]) == (24.7136, 46.6753)

    def test_branch_manager_updates_own_branch(self, client, db, branch):
        manager = make_manager(db, branch)
        response = client.patch(f"/branches/{branch.id}", headers=auth_headers(manager), json={"phone": "+966 13 860 0000"})
        assert response.status_code == 200

    def test_location_can_be_cleared(self, client, db, branch):
        manager = make_manager(db, branch)
        response = client.patch(
            f"/branches/{branch.id}", headers=auth_headers(manager), json={"latitude": None, "longitude": None}
        )
        assert response.json()["latitude"] is None
        assert search(client).json() == []

    @pytest.mark.parametrize("role", [UserRole.MANAGER, UserRole.LAUNDRY])
    def test_staff_of_other_branches_cannot_edit(self, client, db, branch, role):
        if role == UserRole.MANAGER:
            outsider = make_manager(db, make_branch(db))
        else:
            outsider = make_user(db, role)
            make_laundry(db, outsider)
        response = client.patch(f"/branches/{branch.id}", headers=auth_headers(outsider), json={"phone": "0555555555"})
        assert response.status_code == 403

    def test_customers_cannot_edit_branches(self, client, db, branch):
        response = client.patch(f"/branches/{branch.id}", headers=auth_headers(make_user(db)), json={"phone": "0555555555"})
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "changes",
        [{"latitude": 26.3}, {"longitude": 50.1}, {"latitude": 95, "longitude": 50}, {"service_radius_km": 0}],
    )
    def test_invalid_location_updates_are_rejected(self, client, db, branch, changes):
        manager = make_manager(db, branch)
        assert client.patch(f"/branches/{branch.id}", headers=auth_headers(manager), json=changes).status_code == 422

    def test_public_branch_listing_does_not_expose_staff(self, client, db, branch):
        make_manager(db, branch)
        body = client.get(f"/laundries/{branch.laundry_id}/branches").json()
        assert "operators" not in body[0]
