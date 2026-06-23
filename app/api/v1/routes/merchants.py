from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.restaurant import Merchant, MerchantType, Product
from app.schemas.restaurant import (
    MerchantOnboardRequest, MerchantResponse,
    MerchantDetailResponse, ProductCreate, ProductResponse,
)
from app.services.payment_service import register_merchant_subaccount

router = APIRouter(prefix="/merchants", tags=["Merchants"])


# CHANGED — now creates Paystack subaccount before saving to DB
@router.post("/onboard", response_model=MerchantResponse, status_code=201)
def onboard_merchant(
    data:         MerchantOnboardRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role(UserRole.merchant)),
):
    try:
        subaccount_code = register_merchant_subaccount(
            data.business_name, data.bank_code, data.account_number
        )
    except ValueError as e:
        raise HTTPException(502, str(e))

    merchant = Merchant(
        owner_id                 = current_user.id,
        business_name            = data.business_name,
        merchant_type            = data.merchant_type,
        location                 = data.location,
        paystack_subaccount_code = subaccount_code,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@router.get("/restaurants", response_model=List[MerchantResponse])
def list_restaurants(db: Session = Depends(get_db)):
    return db.query(Merchant).filter(
        Merchant.merchant_type == MerchantType.restaurant,
        Merchant.is_active     == True,
    ).all()


@router.get("/liquor-stores", response_model=List[MerchantResponse])
def list_liquor_stores(db: Session = Depends(get_db)):
    return db.query(Merchant).filter(
        Merchant.merchant_type == MerchantType.liquor_store,
        Merchant.is_active     == True,
    ).all()


@router.get("/{merchant_id}", response_model=MerchantDetailResponse)
def get_merchant(merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")
    return merchant


@router.post("/{merchant_id}/products", response_model=ProductResponse, status_code=201)
def add_product(
    merchant_id:  int,
    data:         ProductCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role(UserRole.merchant)),
):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")
    if merchant.owner_id != current_user.id:
        raise HTTPException(403, "You don't own this merchant account")
    product = Product(merchant_id=merchant_id, name=data.name,
                      description=data.description, price=data.price)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product