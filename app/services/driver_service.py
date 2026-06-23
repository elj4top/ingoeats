from datetime import datetime
from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories import order_repo
from app.models.user import User
from app.models.order import Order, OrderStatus

# Valid forward transitions a rider may apply once they hold an order.
RIDER_TRANSITIONS = {
    OrderStatus.ready_for_pickup: OrderStatus.on_the_way,
    OrderStatus.on_the_way:       OrderStatus.delivered,
}


def list_available_deliveries(db: Session) -> List[Order]:
    """Orders that are ready for pickup and not yet claimed by a rider."""
    return order_repo.list_unassigned_ready_for_pickup(db)


def list_my_deliveries(db: Session, rider: User) -> List[Order]:
    return order_repo.list_for_rider(db, rider.id)


def accept_delivery(db: Session, rider: User, order_id: int) -> Order:
    order = order_repo.get_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.rider_id is not None:
        raise HTTPException(status_code=400, detail="Order already assigned to a rider")
    if order.status != OrderStatus.ready_for_pickup:
        raise HTTPException(status_code=400, detail="Order not ready for pickup yet")

    return order_repo.assign_rider(db, order, rider.id)


def update_delivery_status(db: Session, rider: User, order_id: int, new_status: OrderStatus) -> Order:
    order = order_repo.get_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.rider_id != rider.id:
        raise HTTPException(status_code=403, detail="Not your delivery")

    expected_next = RIDER_TRANSITIONS.get(order.status)
    if expected_next != new_status:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition order from {order.status.value} to {new_status.value}",
        )

    order.status = new_status
    # Note: Order has no delivered_at column today. If you want to track delivery
    # timestamps, add `delivered_at = Column(DateTime, nullable=True)` to the
    # Order model first, then set it here.

    db.commit()
    db.refresh(order)
    return order