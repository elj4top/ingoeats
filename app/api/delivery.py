from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/delivery", tags=["Rider Logistics & Delivery"])

# 🏍️ 1. View All Available/Paid Orders in Kakamega
@router.get("/available-orders", response_model=List[schemas.DeliveryOrderResponse])
def get_available_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Fetch all orders that have been successfully PAID via M-Pesa 
    but haven't been picked up by a Boda rider yet.
    """
    # Enforce role safety check
    if current_user.role not in [models.UserRole.RIDER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied. Only registered riders can view this panel.")

    return db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.PAID
    ).all()


# 📥 2. Claim an Order (Rider Accepts the Job)
@router.post("/claim/{order_id}")
def claim_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Assign an active order to the logged-in rider and switch status to PREPARING/ON_THE_WAY.
    """
    if current_user.role not in [models.UserRole.RIDER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only registered riders can claim orders.")

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != models.OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order is already claimed or unavailable")

    # Tie the order row to this specific rider's profile account ID
    order.rider_id = current_user.id
    order.status = models.OrderStatus.PREPARING
    db.commit()

    return {
        "status": "success",
        "message": f"Order #{order.id} claimed successfully by {current_user.full_name}. Proceed to merchant location.",
        "new_status": order.status
    }


# ✅ 3. Mark Order as Delivered (Fulfillment Complete)
@router.post("/complete/{order_id}")
def complete_delivery(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Rider marks the order as delivered once food and liquor are dropped off at MMUST/Corporate location.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.rider_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You are not authorized to complete this delivery.")

    if order.status not in [models.OrderStatus.PREPARING, models.OrderStatus.ON_THE_WAY]:
        raise HTTPException(status_code=400, detail="Order cannot be completed from its current status")

    order.status = models.OrderStatus.DELIVERED
    db.commit()

    return {
        "status": "success",
        "message": f"Order #{order.id} successfully marked as DELIVERED. Earnings added.",
        "final_status": order.status
    }
