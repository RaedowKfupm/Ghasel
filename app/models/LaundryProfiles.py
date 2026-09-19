from sqlalchemy import DateTime
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class LaundryProfile(Base):
    __tablename__ = 'Laundry'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    branches = relationship("LaundryBranch", back_populates="laundry", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="laundry_profile", uselist=False)

class LaundryBranch(Base):
    __tablename__ = 'Branches'
    id = Column(Integer, primary_key=True, index=True)
    laundry_id = Column(Integer, ForeignKey('Laundry.id', ondelete="CASCADE"), nullable=False)
    branch_name = Column(String)
    branch_address = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    laundry = relationship("LaundryProfile", back_populates="branches", uselist=False)
    orders = relationship("Orders", back_populates="branch")

    