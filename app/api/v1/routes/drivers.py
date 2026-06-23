from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.schemas.order import OrderOut, OrderStatusUpdate
from app.services import driver_service

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/deliveries/available", response_model=List[OrderOut])
def available_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.rider)),
):
    return driver_service.list_available_deliveries(db)


@router.get("/deliveries/mine", response_model=List[OrderOut])
def my_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.rider)),
):
    return driver_service.list_my_deliveries(db, current_user)


@router.post("/deliveries/{order_id}/accept", response_model=OrderOut)
def accept_delivery(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.rider)),
):
    return driver_service.accept_delivery(db, current_user, order_id)


@router.patch("/deliveries/{order_id}/status", response_model=OrderOut)
def update_delivery_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.rider)),
):
    return driver_service.update_delivery_status(db, current_user, order_id, data.status)