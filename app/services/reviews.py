"""Verified reviews: only the customer of a completed order may review it, once."""

from sqlalchemy import Float, Select, cast, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.LaundryProfiles import LaundryBranch
from app.models.Orders import Orders
from app.models.Reviews import Review
from app.models.Users import User
from app.schemas.pagination import Pagination
from app.schemas.review import ReviewCreate


def rating_summary() -> Select:
    """Per-branch average rating and review count, computed from the reviews themselves."""
    return (
        select(
            Orders.branch_id.label("branch_id"),
            cast(func.round(func.avg(Review.rating), 2), Float).label("rating_average"),
            func.count(Review.id).label("rating_count"),
        )
        .join(Review, Review.order_id == Orders.id)
        .group_by(Orders.branch_id)
    )


def _review_query() -> Select:
    return select(Review).options(joinedload(Review.order).joinedload(Orders.customer))


def create_review(order_id: int, review_data: ReviewCreate, customer: User, db: Session) -> Review:
    # Another customer's order is reported as missing so order ids cannot be probed.
    order = db.scalar(select(Orders).where(Orders.id == order_id, Orders.customer_id == customer.id))
    if order is None:
        raise NotFoundError("Order not found")
    # COMPLETED is terminal, so this check cannot be invalidated by a concurrent change.
    if order.status != OrderStatus.COMPLETED:
        raise ConflictError("Only completed orders can be reviewed")

    review = Review(order_id=order.id, **review_data.model_dump())
    db.add(review)
    try:
        db.commit()
    except IntegrityError as error:  # uq_reviews_order: a concurrent or repeated review
        db.rollback()
        raise ConflictError("This order has already been reviewed") from error
    return db.scalar(_review_query().where(Review.id == review.id))


def list_branch_reviews(branch_id: int, pagination: Pagination, db: Session) -> list[Review]:
    if db.get(LaundryBranch, branch_id) is None:
        raise NotFoundError("Branch not found")
    return list(
        db.scalars(
            _review_query()
            .join(Orders, Review.order_id == Orders.id)
            .where(Orders.branch_id == branch_id)
            .order_by(Review.created_at.desc(), Review.id.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
    )
