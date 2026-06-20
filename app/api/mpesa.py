""" It handles network requests. 
The /stkpush route verifies the pending payment total and
links it to Safaricom's tracking transaction instance [INDEX].
The public /callback webhook receives secure confirmation 
from Safaricom when a PIN is entered correctly,
immediately updating the order status to PAID so merchants can start cooking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.mpesa_client import MpesaClient

router = APIRouter(prefix="/api/mpesa", tags=["M-Pesa Payments"])
mpesa_service = MpesaClient()

@router.post("/stkpush")
def trigger_payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != models.OrderStatus.PENDING_PAYMENT:
        raise HTTPException(status_code=400, detail="Order is already paid")
        
    customer = db.query(models.User).filter(models.User.id == order.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer missing")

    try:
        response = mpesa_service.initiate_stk_push(
            phone_number=customer.phone_number,
            amount=int(order.total_amount),
            account_reference=f"ORDER-{order.id}"
        )
        if response.get("ResponseCode") == "0":
            checkout_id = response.get("MerchantRequestID") or response.get("CheckoutRequestID")
            order.mpesa_checkout_id = checkout_id
            db.commit()
            return {"status": "success", "checkout_id": checkout_id}
        else:
            raise HTTPException(status_code=400, detail="Safaricom rejected request")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/callback")
async def mpesa_callback(payload: dict, db: Session = Depends(get_db)):
    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    checkout_id = stk_callback.get("CheckoutRequestID")
    
    order = db.query(models.Order).filter(models.Order.mpesa_checkout_id == checkout_id).first()
    if not order:
        return {"ResultCode": 0, "ResultDesc": "Ignored"}

    if result_code == 0:
        order.status = models.OrderStatus.PAID
    else:
        order.status = models.OrderStatus.CANCELLED
        
    db.commit()
    return {"ResultCode": 0, "ResultDesc": "Success"}
