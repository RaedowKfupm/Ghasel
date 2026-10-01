from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.enums import UserRole


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(Enum(UserRole, native_enum=False), nullable=False)
    laundry_id = Column(Integer, ForeignKey("Laundry.id", ondelete="SET NULL"), nullable=True)
    laundry_branch_id = Column(Integer, ForeignKey("Branches.id", ondelete="SET NULL"), nullable=True)
    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    laundry = relationship("LaundryProfile", back_populates="users", foreign_keys=[laundry_id])
    laundry_branch = relationship("LaundryBranch", back_populates="operators", foreign_keys=[laundry_branch_id])
    orders = relationship("Orders", back_populates="customer")


