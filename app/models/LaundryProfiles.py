from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import relationship

from app.core.enums import LaundryRequestStatus
from app.db.base import Base


class LaundryProfile(Base):
    __tablename__ = "Laundry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    branches = relationship("LaundryBranch", back_populates="laundry", cascade="all, delete-orphan")
    users = relationship("User", back_populates="laundry", foreign_keys="User.laundry_id")


class LaundryBranch(Base):
    __tablename__ = "Branches"

    id = Column(Integer, primary_key=True, index=True)
    laundry_id = Column(Integer, ForeignKey("Laundry.id", ondelete="CASCADE"), nullable=False)
    branch_name = Column(String)
    branch_address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    laundry = relationship("LaundryProfile", back_populates="branches", uselist=False)
    operators = relationship("User", back_populates="laundry_branch", foreign_keys="User.laundry_branch_id")
    orders = relationship("Orders", back_populates="branch")


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
