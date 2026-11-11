"""Authentication, role authorization and laundry onboarding ownership."""

import pytest

from app.core.enums import UserRole
from tests.factories import PASSWORD, auth_headers, make_branch, make_laundry, make_user


def register(client, role="customer", email="new@example.com"):
    return client.post(
        "/auth/register",
        json={"name": "New User", "email": email, "password": PASSWORD, "role": role},
    )


class TestAuthentication:
    def test_register_returns_token_that_authenticates(self, client):
        response = register(client)
        assert response.status_code == 201
        token = response.json()["access_token"]

        me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "new@example.com"

    def test_privileged_roles_cannot_self_register(self, client):
        assert register(client, role="admin").status_code == 403
        assert register(client, role="manager").status_code == 403

    @pytest.mark.parametrize(
        "changes",
        [{"password": "short"}, {"name": "   "}, {"email": "not-an-email"}, {"role": "superuser"}],
    )
    def test_registration_input_is_validated(self, client, changes):
        body = {"name": "New User", "email": "new@example.com", "password": PASSWORD, "role": "customer", **changes}
        assert client.post("/auth/register", json=body).status_code == 422

    def test_duplicate_email_is_rejected(self, client):
        register(client)
        assert register(client).status_code == 409

    def test_login_with_wrong_password_is_unauthorized(self, client, db):
        user = make_user(db)
        response = client.post("/auth/login", json={"email": user.email, "password": "wrong"})
        assert response.status_code == 401

    def test_login_with_correct_password(self, client, db):
        user = make_user(db)
        response = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
        assert response.status_code == 200
        assert response.json()["role"] == "customer"

    def test_garbage_and_missing_tokens_are_rejected(self, client):
        assert client.get("/users/me").status_code == 401
        assert client.get("/users/me", headers={"Authorization": "Bearer nope"}).status_code == 401


class TestRoleAuthorization:
    def test_user_listing_is_admin_only(self, client, db):
        customer = make_user(db)
        admin = make_user(db, UserRole.ADMIN)
        assert client.get("/users/", headers=auth_headers(customer)).status_code == 403
        assert client.get("/users/", headers=auth_headers(admin)).status_code == 200

    def test_only_customers_can_store_phone_and_address(self, client, db):
        owner = make_user(db, UserRole.LAUNDRY)
        response = client.patch("/users/me", headers=auth_headers(owner), json={"phone": "0555"})
        assert response.status_code == 422

    @pytest.mark.parametrize("changes", [{"phone": "call me"}, {"name": ""}, {"address": "x"}])
    def test_profile_updates_are_validated(self, client, db, changes):
        customer = make_user(db)
        assert client.patch("/users/me", headers=auth_headers(customer), json=changes).status_code == 422

    def test_customer_profile_update(self, client, db):
        customer = make_user(db)
        response = client.patch(
            "/users/me",
            headers=auth_headers(customer),
            json={"phone": "0555000000", "address": "Dhahran"},
        )
        assert response.status_code == 200
        assert response.json()["address"] == "Dhahran"


class TestLaundryOnboarding:
    def test_application_approval_links_owner_to_named_company(self, client, db):
        owner = make_user(db, UserRole.LAUNDRY)
        admin = make_user(db, UserRole.ADMIN)

        request = client.post("/laundries/", headers=auth_headers(owner), json={"company_name": "Sparkle"})
        assert request.status_code == 201
        approved = client.post(f"/laundries/requests/{request.json()['id']}/approve", headers=auth_headers(admin))
        assert approved.status_code == 201
        assert approved.json()["name"] == "Sparkle"

        again = client.post(f"/laundries/requests/{request.json()['id']}/approve", headers=auth_headers(admin))
        assert again.status_code == 409
        assert client.get("/users/me", headers=auth_headers(owner)).json()["laundry_id"] == approved.json()["id"]

    def test_second_pending_application_is_rejected(self, client, db):
        owner = make_user(db, UserRole.LAUNDRY)
        client.post("/laundries/", headers=auth_headers(owner), json={"company_name": "Alpha Wash"})
        response = client.post("/laundries/", headers=auth_headers(owner), json={"company_name": "Beta Wash"})
        assert response.status_code == 409

    def test_owner_cannot_manage_another_company(self, client, db):
        owner = make_user(db, UserRole.LAUNDRY)
        make_laundry(db, owner)
        other = make_laundry(db, name="Rival")
        branch = {"branch_name": "X", "branch_address": "Y", "phone": "1"}
        response = client.post(f"/laundries/{other.id}/branches", headers=auth_headers(owner), json=branch)
        assert response.status_code == 404

    def test_owner_cannot_assign_manager_to_foreign_branch(self, client, db):
        owner = make_user(db, UserRole.LAUNDRY)
        laundry = make_laundry(db, owner)
        foreign_branch = make_branch(db)
        response = client.post(
            f"/laundries/{laundry.id}/managers",
            headers=auth_headers(owner),
            json={"name": "M", "email": "m@example.com", "password": PASSWORD, "branch_id": foreign_branch.id},
        )
        assert response.status_code == 404

    def test_owner_sees_own_latest_application(self, client, db):
        owner = make_user(db, UserRole.LAUNDRY)
        assert client.get("/laundries/requests/me", headers=auth_headers(owner)).json() is None
        client.post("/laundries/", headers=auth_headers(owner), json={"company_name": "Sparkle"})
        mine = client.get("/laundries/requests/me", headers=auth_headers(owner)).json()
        assert (mine["company_name"], mine["status"]) == ("Sparkle", "pending")
        assert client.get("/laundries/requests/me", headers=auth_headers(make_user(db))).status_code == 403
