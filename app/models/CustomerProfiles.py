from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class CustomerProfile(Base):
    __tablename__ = 'Customers'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True, index=True)
    phone = Column(String, nullable=False)
    address = Column(String)
    
