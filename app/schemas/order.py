from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.order import OrderStatus, DeliveryPaymentStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity:   int


# CHANGED — no customer_id, that comes from the JWT token now
class OrderCreate(BaseModel):
    merchant_id:      int
    delivery_address: str
    items:            List[OrderItemCreate]


class OrderItemOut(BaseModel):
    id:                int
    product_id:        int
    quantity:          int
    price_at_purchase: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id:                  int
    customer_id:         int
    merchant_id:         int
    rider_id:            Optional[int]
    subtotal:            float
    delivery_fee:        float
    service_fee:         float
    total_amount:        float
    status:              OrderStatus
    delivery_address:    str
    created_at:          datetime
    items:               List[OrderItemOut] = []
    paystack_reference:  Optional[str]
    payment_url:         Optional[str]      # returned after order creation so app can redirect customer

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# NEW — returned immediately after POST /orders so the customer knows where to pay
class InitiatePaymentResponse(BaseModel):
    order_id:    int
    reference:   str
    payment_url: str
    amount:      float


# NEW — returned when rider confirms delivery and payout is triggered
class DeliveryConfirmOut(BaseModel):
    order_id:              int
    rider_id:              int
    amount_released:       float
    paystack_transfer_ref: Optional[str]
    status:                DeliveryPaymentStatus

    class Config:
        from_attributes = True