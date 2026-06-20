from pydantic import BaseModel
from typing import Optional, List
from app.models import MerchantType

# --- PRODUCT SCHEMAS ---
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ProductResponse(BaseModel):
    id: int
    merchant_id: int
    name: str
    description: Optional[str]
    price: float
    is_available: int

    class Config:
        from_attributes = True

# --- MERCHANT SCHEMAS ---
class MerchantCreate(BaseModel):
    business_name: str
    merchant_type: MerchantType  # "restaurant" or "liquor_store"
    location: str

class MerchantResponse(BaseModel):
    id: int
    owner_id: Optional[int]
    business_name: str
    merchant_type: MerchantType
    location: str
    is_active: int

    class Config:
        from_attributes = True

class MerchantDetailResponse(MerchantResponse):
    products: List[ProductResponse] = []


# --- ORDER SCHEMAS (Fixes your current crash!) ---
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    delivery_address: str          # e.g., "MMUST Hostel 3, Room 12"
    items: List[OrderItemCreate]   # List of products in the shopping cart
 

# --- AUTHENTICATION SCHEMAS ---
class UserSignup(BaseModel):
    full_name: str
    phone_number: str  # Format: 2547XXXXXXXX
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

# --- DELIVERY SCHEMAS ---
class DeliveryOrderResponse(BaseModel):
    id: int
    subtotal: float
    delivery_fee: float
    total_amount: float
    status: str
    delivery_address: str

    class Config:
        from_attributes = True
