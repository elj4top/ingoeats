from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus, DeliveryPayment, DeliveryPaymentStatus
from app.schemas.order import DeliveryConfirmOut
from app.services.payment_service import release_rider_payment, verify_signature
from app.core.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/webhook", status_code=200)
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if not verify_signature(payload, signature):
        raise HTTPException(401, "Invalid signature")

    data  = await request.json()
    event = data.get("event")

    if event == "charge.success":
        reference = data["data"]["reference"]
        order = db.query(Order).filter(Order.paystack_reference == reference).first()
        if not order or order.status != OrderStatus.pending_payment:
            return {"status": "ignored"}

        order.status = OrderStatus.paid
        db.add(DeliveryPayment(
            order_id = order.id,
            rider_id = order.rider_id,
            amount   = round(order.delivery_fee * settings.RIDER_DELIVERY_SHARE, 2),
            status   = DeliveryPaymentStatus.held,
        ))
        db.commit()

    elif event == "transfer.success":
        ref = data["data"]["transfer_code"]
        dp  = db.query(DeliveryPayment).filter(
            DeliveryPayment.paystack_transfer_ref == ref,
            DeliveryPayment.status == DeliveryPaymentStatus.processing,
        ).first()
        if dp:
            dp.status      = DeliveryPaymentStatus.released
            dp.released_at = datetime.utcnow()
            db.commit()

    elif event in ("transfer.failed", "transfer.reversed"):
        ref = data["data"]["transfer_code"]
        dp  = db.query(DeliveryPayment).filter(
            DeliveryPayment.paystack_transfer_ref == ref,
            DeliveryPayment.status == DeliveryPaymentStatus.processing,
        ).first()
        if dp:
            dp.status = DeliveryPaymentStatus.failed
            db.commit()
            # TODO: notify ops/rider, decide whether order.status should revert
            # from 'delivered' — e.g. to a 'payout_failed' flag for manual review

    return {"status": "ok"}


@router.post("/orders/{order_id}/confirm-delivery", response_model=DeliveryConfirmOut)
def confirm_delivery(
    order_id:     int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role(UserRole.rider)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.rider_id != current_user.id:
        raise HTTPException(403, "You are not the assigned rider")
    if order.status != OrderStatus.on_the_way:
        raise HTTPException(400, f"Order status is '{order.status}', expected 'on_the_way'")
    if not current_user.paystack_recipient_code:
        raise HTTPException(400, "Rider payout account not set up")

    dp = db.query(DeliveryPayment).filter(
        DeliveryPayment.order_id == order_id,
        DeliveryPayment.status   == DeliveryPaymentStatus.held,
    ).first()
    if not dp:
        raise HTTPException(404, "No held payment found for this order")

    try:
        transfer_ref = release_rider_payment(
            recipient_code = current_user.paystack_recipient_code,
            amount_kes     = dp.amount,
            order_id       = order_id,
        )
    except ValueError as e:
        raise HTTPException(502, str(e))

    dp.paystack_transfer_ref = transfer_ref
    dp.status                = DeliveryPaymentStatus.processing
    order.status              = OrderStatus.delivered
    db.commit()
    db.refresh(dp)
    return dp