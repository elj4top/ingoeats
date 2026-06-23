from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name:    str
    phone_number: str
    email:        Optional[EmailStr] = None
    password:     str
    role:         UserRole = UserRole.customer


# NEW — rider-specific registration, collects M-Pesa number for Paystack payout setup
class RiderCreate(BaseModel):
    full_name:    str
    phone_number: str
    email:        Optional[EmailStr] = None
    password:     str


class UserOut(BaseModel):
    id:                      int
    full_name:               str
    phone_number:            str
    email:                   Optional[str]
    role:                    UserRole
    paystack_recipient_code: Optional[str]
    created_at:              datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"