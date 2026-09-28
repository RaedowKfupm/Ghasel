from sqlalchemy import Column, Enum, Integer, String
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
    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    laundry_profile = relationship("LaundryProfile", back_populates="owner", uselist=True)
    orders = relationship("Orders", back_populates="customer")


