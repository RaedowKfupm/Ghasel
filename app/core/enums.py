from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    LAUNDRY = "laundry"
    ADMIN = "admin"
    MANAGER = "manager"


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    READY = "ready"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"