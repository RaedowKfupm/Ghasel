"""Verified reviews: eligibility, uniqueness, validation and rating aggregation."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError
from app.models.Users import User
from app.schemas.review import ReviewCreate
from app.services.reviews import create_review
from tests.factories import ORIGIN, auth_headers, make_branch, make_manager, make_order, make_user


@pytest.fixture
def customer(db):
    return make_user(db, name="Sara Al Qahtani")


@pytest.fixture
def branch(db):
    return make_branch(db)


@pytest.fixture
def completed_order(db, customer, branch):
    return make_order(db, customer, branch, status=OrderStatus.COMPLETED)


def review(client, user, order, **body):
    return client.post(f"/orders/{order.id}/review", headers=auth_headers(user), json={"rating": 5, **body})


class TestEligibility:
    def test_customer_reviews_completed_order(self, client, customer, completed_order):
        response = review(client, customer, completed_order, rating=4, comment="  Crisp shirts, on time.  ")
        assert response.status_code == 201
        body = response.json()
        assert (body["rating"], body["comment"]) == (4, "Crisp shirts, on time.")
        assert body["reviewer_name"] == "Sara Q."

    @pytest.mark.parametrize(
        "status",
        [s for s in OrderStatus if s != OrderStatus.COMPLETED],
    )
    def test_unfinished_or_cancelled_orders_cannot_be_reviewed(self, client, db, customer, branch, status):
        order = make_order(db, customer, branch if status != OrderStatus.PENDING else None, status=status)
        assert review(client, customer, order).status_code == 409

    def test_customer_cannot_review_someone_elses_order(self, client, db, completed_order):
        assert review(client, make_user(db), completed_order).status_code == 404

    def test_branch_staff_cannot_review(self, client, db, branch, completed_order):
        assert review(client, make_manager(db, branch), completed_order).status_code == 403

    def test_order_can_be_reviewed_only_once(self, client, customer, completed_order):
        assert review(client, customer, completed_order).status_code == 201
        assert review(client, customer, completed_order, rating=1).status_code == 409

    def test_simultaneous_reviews_of_one_order_yield_one(self, session_factory, customer, completed_order):
        barrier = threading.Barrier(6)

        def attempt(_):
            with session_factory() as session:
                user = session.get(User, customer.id)
                barrier.wait()
                try:
                    create_review(completed_order.id, ReviewCreate(rating=5), user, session)
                    return True
                except ConflictError:
                    return False

        with ThreadPoolExecutor(max_workers=6) as pool:
            assert sum(pool.map(attempt, range(6))) == 1


class TestValidation:
    @pytest.mark.parametrize("rating", [0, 6, -1, 4.5, None, "great"])
    def test_rating_must_be_whole_number_from_one_to_five(self, client, customer, completed_order, rating):
        assert review(client, customer, completed_order, rating=rating).status_code == 422

    def test_comment_length_is_limited(self, client, customer, completed_order):
        assert review(client, customer, completed_order, comment="x" * 1001).status_code == 422

    def test_blank_comment_is_stored_as_none(self, client, customer, completed_order):
        assert review(client, customer, completed_order, comment="   ").json()["comment"] is None

    def test_database_rejects_out_of_range_rating(self, db, completed_order):
        with pytest.raises(IntegrityError):
            db.execute(text("INSERT INTO reviews (order_id, rating) VALUES (:id, 9)"), {"id": completed_order.id})
            db.commit()
        db.rollback()


class TestRatings:
    def _completed(self, db, branch, count):
        return [make_order(db, make_user(db), branch, status=OrderStatus.COMPLETED) for _ in range(count)]

    def _review_all(self, client, db, orders, ratings):
        for order, rating in zip(orders, ratings, strict=True):
            customer = db.get(User, order.customer_id)
            assert review(client, customer, order, rating=rating).status_code == 201

    def test_unreviewed_branch_has_no_rating(self, client, branch):
        body = client.get(f"/branches/{branch.id}").json()
        assert (body["rating_average"], body["rating_count"]) == (None, 0)

    def test_branch_rating_is_mean_of_its_reviews(self, client, db, branch):
        self._review_all(client, db, self._completed(db, branch, 3), [5, 4, 4])
        body = client.get(f"/branches/{branch.id}").json()
        assert body["rating_count"] == 3
        assert body["rating_average"] == pytest.approx(4.33, abs=0.005)

    def test_reviews_count_only_towards_their_own_branch(self, client, db, branch):
        other = make_branch(db)
        self._review_all(client, db, self._completed(db, branch, 1), [5])
        self._review_all(client, db, self._completed(db, other, 2), [1, 2])
        assert client.get(f"/branches/{branch.id}").json()["rating_average"] == 5
        assert client.get(f"/branches/{other.id}").json()["rating_average"] == 1.5

    def test_nearby_results_carry_ratings(self, client, db, branch):
        self._review_all(client, db, self._completed(db, branch, 2), [3, 4])
        nearby = client.get("/branches/nearby", params={"latitude": ORIGIN[0], "longitude": ORIGIN[1]}).json()
        assert (nearby[0]["rating_average"], nearby[0]["rating_count"]) == (3.5, 2)

    def test_branch_reviews_are_listed_newest_first(self, client, db, branch):
        self._review_all(client, db, self._completed(db, branch, 3), [2, 3, 4])
        listed = client.get(f"/branches/{branch.id}/reviews").json()
        assert [r["rating"] for r in listed] == [4, 3, 2]

    def test_reviews_of_unknown_branch_is_not_found(self, client):
        assert client.get("/branches/999/reviews").status_code == 404

    def test_order_detail_shows_its_review(self, client, customer, completed_order):
        review(client, customer, completed_order, rating=4)
        detail = client.get(f"/orders/{completed_order.id}", headers=auth_headers(customer)).json()
        assert detail["review"]["rating"] == 4

    def test_order_listing_shows_which_orders_are_reviewed(self, client, db, customer, branch, completed_order):
        unreviewed = make_order(db, customer, branch, status=OrderStatus.COMPLETED)
        review(client, customer, completed_order, rating=5)
        listed = {o["id"]: o["review"] for o in client.get("/orders/", headers=auth_headers(customer)).json()}
        assert listed[completed_order.id]["rating"] == 5
        assert listed[unreviewed.id] is None
