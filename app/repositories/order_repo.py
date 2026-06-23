from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus, DeliveryPayment, DeliveryPaymentStatus


def create_order(db: Session, customer_id: int, merchant_id: int, delivery_address: str) -> Order:
    order = Order(customer_id=customer_id, merchant_id=merchant_id, delivery_address=delivery_address)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def add_order_item(db: Session, order_id: int, product_id: int, quantity: int, price_at_purchase: float) -> OrderItem:
    item = OrderItem(
        order_id=order_id, product_id=product_id,
        quantity=quantity, price_at_purchase=price_at_purchase,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_total(db: Session, order: Order, total: float) -> Order:
    order.total_amount = total
    db.commit()
    db.refresh(order)
    return order


def get_by_id(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def list_for_customer(db: Session, customer_id: int) -> List[Order]:
    return db.query(Order).filter(Order.customer_id == customer_id).all()


def list_for_merchant(db: Session, merchant_id: int) -> List[Order]:
    return db.query(Order).filter(Order.merchant_id == merchant_id).all()


def list_for_rider(db: Session, rider_id: int) -> List[Order]:
    return db.query(Order).filter(Order.rider_id == rider_id).all()


def list_unassigned_ready_for_pickup(db: Session) -> List[Order]:
    """Orders ready for pickup that no rider has claimed yet."""
    return db.query(Order).filter(
        Order.status == OrderStatus.ready_for_pickup,
        Order.rider_id.is_(None),
    ).all()


def assign_rider(db: Session, order: Order, rider_id: int) -> Order:
    order.rider_id = rider_id
    db.commit()
    db.refresh(order)
    return order


def update_status(db: Session, order: Order, status: OrderStatus) -> Order:
    order.status = status
    db.commit()
    db.refresh(order)
    return order


def create_delivery_payment(db: Session, order_id: int, rider_id: int, amount: float) -> DeliveryPayment:
    payment = DeliveryPayment(
        order_id=order_id, rider_id=rider_id, amount=amount,
        status=DeliveryPaymentStatus.held,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_delivery_payment_by_order(db: Session, order_id: int) -> Optional[DeliveryPayment]:
    return db.query(DeliveryPayment).filter(DeliveryPayment.order_id == order_id).first()


def list_held_delivery_payments(db: Session) -> List[DeliveryPayment]:
    return db.query(DeliveryPayment).filter(DeliveryPayment.status == DeliveryPaymentStatus.held).all()