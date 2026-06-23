from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    merchant = "merchant"
    rider    = "rider"
    admin    = "admin"


class User(Base):
    __tablename__ = "users"

    id                      = Column(Integer, primary_key=True, index=True)
    full_name               = Column(String, nullable=False)
    phone_number            = Column(String, unique=True, index=True, nullable=False)
    email                   = Column(String, unique=True, nullable=True)
    hashed_password         = Column(String, nullable=False)
    role                    = Column(Enum(UserRole), default=UserRole.customer)
    created_at              = Column(DateTime, default=datetime.utcnow)
    # for riders only, stores their M-Pesa payout destination in Paystack
    paystack_recipient_code = Column(String, nullable=True)