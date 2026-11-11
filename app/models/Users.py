from sqlalchemy import CheckConstraint, Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.enums import UserRole
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('CUSTOMER', 'LAUNDRY', 'ADMIN', 'MANAGER')", name="ck_users_role"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole, native_enum=False, length=None), nullable=False)
    laundry_id = Column(Integer, ForeignKey("Laundry.id", ondelete="SET NULL"), nullable=True)
    laundry_branch_id = Column(Integer, ForeignKey("Branches.id", ondelete="SET NULL"), nullable=True)

    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    laundry = relationship("LaundryProfile", back_populates="users", foreign_keys=[laundry_id])
    laundry_branch = relationship("LaundryBranch", back_populates="operators", foreign_keys=[laundry_branch_id])
    orders = relationship("Orders", back_populates="customer")
