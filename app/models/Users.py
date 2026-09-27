from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    laundry_profile = relationship("LaundryProfile", back_populates="owner", uselist=True)
    orders = relationship("Orders", back_populates="customer")


