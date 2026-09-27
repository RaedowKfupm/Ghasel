from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("Branches.id"), nullable=False)
    details = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    completed_at = Column(DateTime)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    customer = relationship("User", back_populates="orders", uselist=False)
    branch = relationship("LaundryBranch", back_populates="orders", uselist=False)