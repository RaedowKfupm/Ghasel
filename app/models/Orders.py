from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import relationship

from app.core.enums import OrderStatus
from app.db.base import Base


class Orders(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'DELIVERING', 'COMPLETED', 'CANCELLED')",
            name="ck_orders_status",
        ),
        CheckConstraint(
            "branch_id IS NOT NULL OR status IN ('PENDING', 'CANCELLED')",
            name="ck_orders_branch_assigned",
        ),
        Index("ix_orders_customer_created", "customer_id", text("created_at DESC")),
        Index("ix_orders_branch_created", "branch_id", text("created_at DESC")),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # NULL while the order is on the marketplace waiting for a branch to accept it.
    branch_id = Column(Integer, ForeignKey("Branches.id"), nullable=True)
    details = Column(String, nullable=False)
    status = Column(Enum(OrderStatus, native_enum=False, length=None), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    customer = relationship("User", back_populates="orders", uselist=False)
    branch = relationship("LaundryBranch", back_populates="orders", uselist=False)
