from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Review(Base):
    """A customer's review of a completed order; the branch is the order's branch."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_reviews_order"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    rating = Column(SmallInteger, nullable=False)
    comment = Column(String(1000))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    order = relationship("Orders", back_populates="review")

    @property
    def reviewer_name(self) -> str:
        first, *rest = self.order.customer.name.split()
        return f"{first} {rest[-1][0]}." if rest else first
