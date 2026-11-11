from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import deferred, relationship

from app.core.enums import LaundryRequestStatus
from app.db.base import Base
from app.db.spatial import GeographyPoint, generated_point


class LaundryProfile(Base):
    __tablename__ = "Laundry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    branches = relationship("LaundryBranch", back_populates="laundry", cascade="all, delete-orphan")
    users = relationship("User", back_populates="laundry", foreign_keys="User.laundry_id")


class LaundryBranch(Base):
    __tablename__ = "Branches"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_branches_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_branches_longitude"),
        CheckConstraint("(latitude IS NULL) = (longitude IS NULL)", name="ck_branches_coordinates_paired"),
        CheckConstraint(
            "service_radius_km > 0 AND service_radius_km <= 100", name="ck_branches_service_radius"
        ),
        Index("ix_branches_location", "location", postgresql_using="gist"),
    )

    id = Column(Integer, primary_key=True, index=True)
    laundry_id = Column(Integer, ForeignKey("Laundry.id", ondelete="CASCADE"), nullable=False)
    branch_name = Column(String)
    branch_address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    # Marketplace orders whose pickup point lies within this radius are offered to the branch.
    service_radius_km = Column(Float, nullable=False, server_default="10")
    location = deferred(Column(GeographyPoint(), generated_point("latitude", "longitude")))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    laundry = relationship("LaundryProfile", back_populates="branches", uselist=False)
    operators = relationship("User", back_populates="laundry_branch", foreign_keys="User.laundry_branch_id")
    orders = relationship("Orders", back_populates="branch")

    @property
    def laundry_name(self) -> str:
        return self.laundry.name


class LaundryRequest(Base):
    __tablename__ = "laundry_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')", name="ck_laundry_requests_status"
        ),
        Index(
            "uq_laundry_requests_one_pending_per_owner",
            "owner_id",
            unique=True,
            postgresql_where=text("status = 'PENDING'"),
        ),
    )

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String, nullable=False)
    status = Column(
        Enum(LaundryRequestStatus, native_enum=False, length=None),
        nullable=False,
        default=LaundryRequestStatus.PENDING,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    decided_at = Column(DateTime(timezone=True))
    laundry_id = Column(Integer, ForeignKey("Laundry.id", ondelete="SET NULL"))
