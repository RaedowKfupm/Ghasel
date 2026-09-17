from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Orders(Base):
    __tablename__ = "Orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    Laundry_id = Column(Integer, ForeignKey("Laundry.id"), nullable=False)
    details = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    completed_at = Column(DateTime)