"""This is the skeletal frame of your business logic.
By separating financial columns (subtotal, delivery_fee, and service_fee)
inside the Order table, your system can automatically calculate exactly
what to payout to your merchants and Boda-Boda riders at the end of the day."""

import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    RIDER = "rider"
    ADMIN = "admin"

class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class MerchantType(str, enum.Enum):
    RESTAURANT = "restaurant"
    LIQUOR_STORE = "liquor_store"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False) # Must be format: 2547XXXXXXXX
    email = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    created_at = Column(DateTime, default=datetime.utcnow)

class Merchant(Base):
    __tablename__ = "merchants"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    business_name = Column(String, nullable=False)
    merchant_type = Column(Enum(MerchantType), nullable=False) # Restaurant or Liquor Store
    location = Column(String, nullable=False)                  # e.g., "Mumias Road", "MMUST Main Gate"
    is_active = Column(Integer, default=1)                     # 1 = Open, 0 = Closed
    commission_rate = Column(Float, default=10.0)              # Percentage marketplace takes
    
    products = relationship("Product", back_populates="merchant")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"))
    name = Column(String, nullable=False)                      # e.g., "Chips Choma" or "Gilbey's Gin 750ml"
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)                      # Base retail price
    is_available = Column(Integer, default=1)
    
    merchant = relationship("Merchant", back_populates="products")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"))
    rider_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Assigned later via logistics
    
    # Financial breakdowns for your marketplace math
    subtotal = Column(Float, nullable=False)                   # Raw food + alcohol cost
    delivery_fee = Column(Float, nullable=False)               # Goes mostly to rider
    service_fee = Column(Float, default=30.0)                  # Fixed platform fee
    total_amount = Column(Float, nullable=False)              # Subtotal + Delivery + Service
    
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING_PAYMENT)
    mpesa_checkout_id = Column(String, nullable=True, unique=True) # Tied to Safaricom Daraja
    delivery_address = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)          # Safety check if prices change later