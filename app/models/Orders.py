from sqlalchemy import CheckConstraint, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import deferred, relationship

from app.core.enums import OrderStatus
from app.db.base import Base
from app.db.spatial import GeographyPoint, generated_point

ORDER_STATUS_SQL = ", ".join(f"'{status.name}'" for status in OrderStatus)


class Orders(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(f"status IN ({ORDER_STATUS_SQL})", name="ck_orders_status"),
        CheckConstraint(
            "branch_id IS NOT NULL OR status IN ('PENDING', 'CANCELLED')",
            name="ck_orders_branch_assigned",
        ),
        CheckConstraint("pickup_latitude BETWEEN -90 AND 90", name="ck_orders_pickup_latitude"),
        CheckConstraint("pickup_longitude BETWEEN -180 AND 180", name="ck_orders_pickup_longitude"),
        CheckConstraint(
            "(pickup_latitude IS NULL) = (pickup_longitude IS NULL)",
            name="ck_orders_pickup_coordinates_paired",
        ),
        CheckConstraint(
            "branch_id IS NOT NULL OR status = 'CANCELLED' OR pickup_latitude IS NOT NULL",
            name="ck_orders_marketplace_has_pickup",
        ),
        Index("ix_orders_customer_created", "customer_id", text("created_at DESC")),
        Index("ix_orders_branch_created", "branch_id", text("created_at DESC")),
        Index(
            "ix_orders_marketplace_pickup",
            "pickup_location",
            postgresql_using="gist",
            postgresql_where=text("status = 'PENDING' AND branch_id IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # NULL while the order is on the marketplace waiting for a branch to accept it.
    branch_id = Column(Integer, ForeignKey("Branches.id"), nullable=True)
    details = Column(String, nullable=False)
    pickup_address = Column(String)
    pickup_latitude = Column(Float)
    pickup_longitude = Column(Float)
    pickup_location = deferred(Column(GeographyPoint(), generated_point("pickup_latitude", "pickup_longitude")))
    status = Column(Enum(OrderStatus, native_enum=False, length=None), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    customer = relationship("User", back_populates="orders", uselist=False)
    branch = relationship("LaundryBranch", back_populates="orders", uselist=False)
    events = relationship(
        "OrderStatusEvent",
        back_populates="order",
        order_by="(OrderStatusEvent.created_at, OrderStatusEvent.id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OrderStatusEvent(Base):
    """One row per status an order entered: an append-only tracking history."""

    __tablename__ = "order_status_events"
    __table_args__ = (
        CheckConstraint(f"status IN ({ORDER_STATUS_SQL})", name="ck_order_status_events_status"),
        Index("ix_order_status_events_order", "order_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(OrderStatus, native_enum=False, length=None), nullable=False)
    # NULL for system-reconstructed history or if the acting user was deleted.
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    order = relationship("Orders", back_populates="events")
    actor = relationship("User")

    @property
    def actor_role(self):
        return self.actor.role if self.actor is not None else None
