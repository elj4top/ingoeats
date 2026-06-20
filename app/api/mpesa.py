"""this file connects the webpage's checkout button to the Mpesa client
 service(mpesa_client.py) its the MPESA API router
 it handles critical things :initiating the payment pop up on the customers
 phone when they place and order 
 and  Recieving call back confirmation from safaricoms server the exact
 time the user types their mpesa pin
 """

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.services.mpesa_client import MpesaClient

router = APIRouter(prefix="/api/mpesa", tags=["M-Pesa Payments"])
mpesa_service = MpesaClient()

@router.post("/stkpush", status_code=status.HTTP_200_OK)
def trigger_payment(order_id: int, db: Session = Depends(get_db)):
    """
    Trigger an M-Pesa STK Push popup on a customer's phone for an unpaid order.
    """
    # Fetch the order from the database
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != models.OrderStatus.PENDING_PAYMENT:
        raise HTTPException(status_code=400, detail="Order is already paid or processed")
        
    # Fetch the customer's phone number
    customer = db.query(models.User).filter(models.User.id == order.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer associated with order not found")

    try:
        # Call the Safaricom Daraja client we built earlier
        account_ref = f"ORDER-{order.id}"
        response = mpesa_service.initiate_stk_push(
            phone_number=customer.phone_number,
            amount=int(order.total_amount),
            account_reference=account_ref
        )
        
        # Check if Safaricom accepted the push request successfully
        if response.get("ResponseCode") == "0":
            checkout_id = response.get("MerchantRequestID") or response.get("CheckoutRequestID")
            
            # Save the checkout ID into the order table to track it during callback
            order.mpesa_checkout_id = checkout_id
            db.commit()
            
            return {
                "status": "success",
                "message": "STK Push sent successfully to the phone",
                "checkout_id": checkout_id
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Safaricom rejected request: {response.get('ResponseDescription')}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"M-Pesa integration error: {str(e)}")


@router.post("/callback")
async def mpesa_callback(payload: dict, db: Session = Depends(get_db)):
    """
    This public URL is pinged directly by Safaricom's servers. 
    It processes payment completion and updates order status.
    """
    # Parse the standard incoming Safaricom nesting structure
    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    checkout_id = stk_callback.get("CheckoutRequestID")
    
    # 1. Locate the corresponding order via the checkout ID
    order = db.query(models.Order).filter(models.Order.mpesa_checkout_id == checkout_id).first()
    if not order:
        # Return 200 to Safaricom anyway so they don't retrying sending an obsolete webhook
        return {"status": "ignored", "message": "Order reference not tracked"}

    # 2. ResultCode == 0 means SUCCESSFUL payment transaction
    if result_code == 0:
        order.status = models.OrderStatus.PAID
        db.commit()
        
        # TODO: Trigger your Africa's Talking API here to SMS the nearest Boda rider!
        print(f"Payment successful for Order #{order.id}. Order status changed to PAID.")
        
    else:
        # The user cancelled, timed out, or had insufficient funds
        order.status = models.OrderStatus.CANCELLED
        db.commit()
        print(f"Payment failed for Order #{order.id}. Code: {result_code}, Reason: {stk_callback.get('ResultDesc')}")

    # Safaricom requires a clean JSON acknowledgment dictionary
    return {"ResultCode": 0, "ResultDesc": "Callback processed successfully"}

