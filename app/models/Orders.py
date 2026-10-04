from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.enums import OrderStatus


class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("Branches.id"), nullable=True)
    details = Column(String, nullable=False)
    status = Column(Enum(OrderStatus, native_enum=False), nullable=False)
    created_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    completed_at = Column(DateTime)
    customer = relationship("User", back_populates="orders", uselist=False)
    branch = relationship("LaundryBranch", back_populates="orders", uselist=False)