from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class MerchantType(str, enum.Enum):
    restaurant   = "restaurant"
    liquor_store = "liquor_store"


class Merchant(Base):
    __tablename__ = "merchants"

    id              = Column(Integer, primary_key=True, index=True)
    owner_id        = Column(Integer, ForeignKey("users.id"))
    business_name   = Column(String, nullable=False)
    merchant_type   = Column(Enum(MerchantType), nullable=False)
    location        = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)
    commission_rate = Column(Float, default=10.0)
    # Registered when merchant signs up, used to auto-split their 90% on every payment
    paystack_subaccount_code = Column(String, nullable=True)

    owner    = relationship("User", foreign_keys=[owner_id])
    products = relationship("Product", back_populates="merchant")
    orders   = relationship("Order", back_populates="merchant")


class Product(Base):
    __tablename__ = "products"

    id           = Column(Integer, primary_key=True, index=True)
    merchant_id  = Column(Integer, ForeignKey("merchants.id"))
    name         = Column(String, nullable=False)
    description  = Column(String, nullable=True)
    price        = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)

    merchant    = relationship("Merchant", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")