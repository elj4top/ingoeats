from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.api.auth import get_current_user # Injects token verification lock!

router = APIRouter(prefix="/api/orders", tags=["Orders & Checkout"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def checkout_cart(
    order_data: schemas.OrderCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) 
):
    """
    Process cart checkout for LOGGED-IN users only.
    Calculates marketplace math and initiates an unpaid base order.
    """
    if not order_data.items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")

    running_subtotal = 0.0
    items_to_save = []

    # Iterate through items to verify existence and calculate prices dynamically
    for item in order_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} does not exist")
        
        if product.is_available == 0:
            raise HTTPException(status_code=400, detail=f"Item '{product.name}' is currently sold out")

        item_cost = product.price * item.quantity
        running_subtotal += item_cost

        # Queue the data entry for the OrderItem table
        order_item = models.OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            price_at_purchase=product.price
        )
        items_to_save.append(order_item)

    # Logistical calculations
    service_fee = 30.0   
    delivery_fee = 100.0 
    final_total = running_subtotal + service_fee + delivery_fee

    # Generate the base unpaid order row entry linked to the secure token user id
    db_order = models.Order(
        customer_id=current_user.id, 
        subtotal=running_subtotal,
        delivery_fee=delivery_fee,
        service_fee=service_fee,
        total_amount=final_total,
        delivery_address=order_data.delivery_address,
        status=models.OrderStatus.PENDING_PAYMENT
    )
    
    db.add(db_order)
    db.commit() 
    db.refresh(db_order)

    # Connect the individual products to the generated order ID
    for order_item in items_to_save:
        order_item.order_id = db_order.id
        db.add(order_item)
    
    db.commit()

    return {
        "status": "success",
        "message": f"Order created successfully for {current_user.full_name}. Ready for payment routing.",
        "order_id": db_order.id,
        "total_payable_ksh": db_order.total_amount
    }
