import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import Merchant, Product
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate, InitiatePaymentResponse
from app.services.payment_service import initiate_payment
from app.core.config import settings

router = APIRouter(prefix="/orders", tags=["Orders"])


# CHANGED — now calculates import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import Merchant, Product
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate, InitiatePaymentResponse
from app.services.payment_service import initiate_payment
from app.core.config import settings

router = APIRouter(prefix="/orders", tags=["Orders"])


# Valid forward transitions per role. Anything not listed here is rejected.
MERCHANT_TRANSITIONS = {
    OrderStatus.paid:             {OrderStatus.preparing},
    OrderStatus.preparing:        {OrderStatus.ready_for_pickup},
}

RIDER_TRANSITIONS = {
    OrderStatus.ready_for_pickup: {OrderStatus.on_the_way},
    OrderStatus.on_the_way:       {OrderStatus.delivered},
}


# CHANGED — now calculates the bill and calls Paystack to get payment URL
@router.post("", response_model=InitiatePaymentResponse, status_code=201)
def place_order(
    data:         OrderCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role(UserRole.customer)),
):
    merchant = db.query(Merchant).filter(
        Merchant.id == data.merchant_id, Merchant.is_active == True
    ).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found or closed")
    if not merchant.paystack_subaccount_code:
        raise HTTPException(400, "Merchant has not completed payment onboarding")

    subtotal    = 0.0
    order_lines = []
    for item in data.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.merchant_id == data.merchant_id,
            Product.is_available == True,
        ).first()
        if not product:
            raise HTTPException(404, f"Product {item.product_id} not available")
        subtotal += product.price * item.quantity
        order_lines.append((product, item.quantity))

    service_fee  = round(subtotal * settings.PLATFORM_COMMISSION_RATE, 2)
    delivery_fee = settings.DELIVERY_FEE
    total_amount = round(subtotal + service_fee + delivery_fee, 2)
    reference    = f"ing_{uuid.uuid4().hex[:12]}"

    order = Order(
        customer_id      = current_user.id,
        merchant_id      = data.merchant_id,
        delivery_address = data.delivery_address,
        subtotal         = subtotal,
        delivery_fee     = delivery_fee,
        service_fee      = service_fee,
        total_amount     = total_amount,
        paystack_reference = reference,
    )
    db.add(order)
    db.flush()

    for product, quantity in order_lines:
        db.add(OrderItem(
            order_id=order.id, product_id=product.id,
            quantity=quantity, price_at_purchase=product.price,
        ))
    db.commit()
    db.refresh(order)

    email = current_user.email or f"{current_user.phone_number}@ingoeats.co.ke"
    try:
        paystack_data = initiate_payment(
            email=email, amount_kes=total_amount,
            reference=reference, subaccount_code=merchant.paystack_subaccount_code,
            order_id=order.id,
        )
    except ValueError as e:
        db.delete(order)
        db.commit()
        raise HTTPException(502, str(e))

    order.paystack_access_code = paystack_data["access_code"]
    db.commit()

    return InitiatePaymentResponse(
        order_id=order.id, reference=reference,
        payment_url=paystack_data["authorization_url"], amount=total_amount,
    )


@router.get("", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.customer_id == current_user.id).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if current_user.role == UserRole.customer and order.customer_id != current_user.id:
        raise HTTPException(403, "Not your order")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(
    order_id: int, data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    # Only the owning merchant or the assigned rider may change order status.
    # Customers and unrelated merchants/riders are blocked.
    if current_user.role == UserRole.merchant:
        if order.merchant.owner_id != current_user.id:
            raise HTTPException(403, "Not your merchant account's order")
        allowed = MERCHANT_TRANSITIONS.get(order.status, set())
    elif current_user.role == UserRole.rider:
        if order.rider_id != current_user.id:
            raise HTTPException(403, "Not your assigned delivery")
        allowed = RIDER_TRANSITIONS.get(order.status, set())
    elif current_user.role == UserRole.admin:
        # Admins can force any transition for support/dispute resolution.
        allowed = set(OrderStatus)
    else:
        raise HTTPException(403, "Customers cannot update order status")

    if data.status not in allowed:
        raise HTTPException(
            400, f"Cannot transition order from {order.status.value} to {data.status.value}"
        )

    order.status = data.status
    db.commit()
    db.refresh(order)
    return 
@router.post("", response_model=InitiatePaymentResponse, status_code=201)
def place_order(
    data:         OrderCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role(UserRole.customer)),
):
    merchant = db.query(Merchant).filter(
        Merchant.id == data.merchant_id, Merchant.is_active == True
    ).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found or closed")
    if not merchant.paystack_subaccount_code:
        raise HTTPException(400, "Merchant has not completed payment onboarding")

    subtotal    = 0.0
    order_lines = []
    for item in data.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.merchant_id == data.merchant_id,
            Product.is_available == True,
        ).first()
        if not product:
            raise HTTPException(404, f"Product {item.product_id} not available")
        subtotal += product.price * item.quantity
        order_lines.append((product, item.quantity))

    service_fee  = round(subtotal * settings.PLATFORM_COMMISSION_RATE, 2)
    delivery_fee = settings.DELIVERY_FEE
    total_amount = round(subtotal + service_fee + delivery_fee, 2)
    reference    = f"ing_{uuid.uuid4().hex[:12]}"

    order = Order(
        customer_id      = current_user.id,
        merchant_id      = data.merchant_id,
        delivery_address = data.delivery_address,
        subtotal         = subtotal,
        delivery_fee     = delivery_fee,
        service_fee      = service_fee,
        total_amount     = total_amount,
        paystack_reference = reference,
    )
    db.add(order)
    db.flush()

    for product, quantity in order_lines:
        db.add(OrderItem(
            order_id=order.id, product_id=product.id,
            quantity=quantity, price_at_purchase=product.price,
        ))
    db.commit()
    db.refresh(order)

    email = current_user.email or f"{current_user.phone_number}@ingoeats.co.ke"
    try:
        paystack_data = initiate_payment(
            email=email, amount_kes=total_amount,
            reference=reference, subaccount_code=merchant.paystack_subaccount_code,
            order_id=order.id,
        )
    except ValueError as e:
        db.delete(order)
        db.commit()
        raise HTTPException(502, str(e))

    order.paystack_access_code = paystack_data["access_code"]
    db.commit()

    return InitiatePaymentResponse(
        order_id=order.id, reference=reference,
        payment_url=paystack_data["authorization_url"], amount=total_amount,
    )


@router.get("", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.customer_id == current_user.id).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if current_user.role == UserRole.customer and order.customer_id != current_user.id:
        raise HTTPException(403, "Not your order")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(
    order_id: int, data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order