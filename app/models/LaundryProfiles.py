from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.enums import LaundryRequestStatus



class LaundryProfile(Base):
    __tablename__ = 'Laundry'
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False)
    branches = relationship("LaundryBranch", back_populates="laundry", cascade="all, delete-orphan")
    users = relationship("User", back_populates="laundry", foreign_keys="User.laundry_id")

class LaundryBranch(Base):
    __tablename__ = 'Branches'
    id = Column(Integer, primary_key=True, index=True)
    laundry_id = Column(Integer, ForeignKey('Laundry.id', ondelete="CASCADE"), nullable=False)
    branch_name = Column(String)
    branch_address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    laundry = relationship("LaundryProfile", back_populates="branches", uselist=False)
    operators = relationship("User", back_populates="laundry_branch", foreign_keys="User.laundry_branch_id")
    orders = relationship("Orders", back_populates="branch")


class LaundryRequest(Base):
    __tablename__ = "laundry_requests"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String, nullable=False)
    status = Column(
        Enum(LaundryRequestStatus, native_enum=False),
        nullable=False,
        default=LaundryRequestStatus.PENDING,
    )
    created_at = Column(DateTime, nullable=False)
    decided_at = Column(DateTime)
    laundry_id = Column(Integer, ForeignKey("Laundry.id", ondelete="SET NULL"))
    

