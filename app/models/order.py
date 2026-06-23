from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class OrderStatus(str, enum.Enum):
    pending_payment  = "pending_payment"
    paid             = "paid"
    preparing        = "preparing"
    ready_for_pickup = "ready_for_pickup"
    on_the_way       = "on_the_way"
    delivered        = "delivered"
    cancelled        = "cancelled"


class DeliveryPaymentStatus(str, enum.Enum):
    held       = "held"        # sitting in your Paystack balance
    processing = "processing"  # transfer initiated, awaiting Paystack confirmation
    released   = "released"    # confirmed sent to rider's M-Pesa
    failed     = "failed"      # transfer failed or was reversed
    refunded   = "refunded"    # order cancelled

class Order(Base):
    __tablename__ = "orders"

    id               = Column(Integer, primary_key=True, index=True)
    customer_id      = Column(Integer, ForeignKey("users.id"))
    merchant_id      = Column(Integer, ForeignKey("merchants.id"))
    rider_id         = Column(Integer, ForeignKey("users.id"), nullable=True)
    subtotal         = Column(Float, nullable=False)
    delivery_fee     = Column(Float, nullable=False)
    service_fee      = Column(Float, nullable=False)
    total_amount     = Column(Float, nullable=False)
    status           = Column(Enum(OrderStatus), default=OrderStatus.pending_payment)
    delivery_address = Column(String, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
   
    paystack_reference   = Column(String, nullable=True, unique=True)
    paystack_access_code = Column(String, nullable=True)

    merchant         = relationship("Merchant", back_populates="orders", foreign_keys=[merchant_id])
    items            = relationship("OrderItem", back_populates="order")
    delivery_payment = relationship("DeliveryPayment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id                = Column(Integer, primary_key=True, index=True)
    order_id          = Column(Integer, ForeignKey("orders.id"))
    product_id        = Column(Integer, ForeignKey("products.id"))
    quantity          = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    order   = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class DeliveryPayment(Base):
    __tablename__ = "delivery_payments"

    id                    = Column(Integer, primary_key=True, index=True)
    order_id              = Column(Integer, ForeignKey("orders.id"), unique=True)
    rider_id              = Column(Integer, ForeignKey("users.id"))
    amount                = Column(Float, nullable=False)
    status                = Column(Enum(DeliveryPaymentStatus), default=DeliveryPaymentStatus.held)
    created_at            = Column(DateTime, default=datetime.utcnow)
    released_at           = Column(DateTime, nullable=True)
    paystack_transfer_ref = Column(String, nullable=True)

    order = relationship("Order", back_populates="delivery_payment")