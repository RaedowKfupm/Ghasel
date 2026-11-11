from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class CustomerProfile(Base):
    __tablename__ = 'Customers'
    id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True, index=True)
    phone = Column(String, nullable=False)
    address = Column(String)
    user = relationship("User", back_populates="customer_profile", uselist=False)
