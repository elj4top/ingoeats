from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/merchants", tags=["Merchants & Menus"])

# 🏢 1. Register a New Merchant (Restaurant or Liquor Store)
@router.post("/", response_model=schemas.MerchantResponse, status_code=status.HTTP_201_CREATED)
def create_merchant(merchant: schemas.MerchantCreate, db: Session = Depends(get_db)):
    """
    Register a new store into the IngoEats marketplace ecosystem.
    """
    db_merchant = models.Merchant(
        business_name=merchant.business_name,
        merchant_type=merchant.merchant_type,
        location=merchant.location,
        owner_id=1  # Hardcoded placeholder user ID until Authentication logic is completed
    )
    db.add(db_merchant)
    db.commit()
    db.refresh(db_merchant)
    return db_merchant


# 🍔 2. List All Active Restaurants
@router.get("/restaurants", response_model=List[schemas.MerchantResponse])
def get_restaurants(db: Session = Depends(get_db)):
    """
    Fetch all active food joints in Kakamega for hungry customers/students.
    """
    return db.query(models.Merchant).filter(
        models.Merchant.merchant_type == models.MerchantType.RESTAURANT,
        models.Merchant.is_active == 1
    ).all()


# 🍾 3. List All Active Liquor Stores
@router.get("/liquor-stores", response_model=List[schemas.MerchantResponse])
def get_liquor_stores(db: Session = Depends(get_db)):
    """
    Fetch active wine & spirits outlets in town.
    """
    return db.query(models.Merchant).filter(
        models.Merchant.merchant_type == models.MerchantType.LIQUOR_STORE,
        models.Merchant.is_active == 1
    ).all()


# 📜 4. Get a Specific Store's Menu / Inventory
@router.get("/{merchant_id}", response_model=schemas.MerchantDetailResponse)
def get_merchant_menu(merchant_id: int, db: Session = Depends(get_db)):
    """
    Retrieve details of a specific store alongside all its listed items.
    """
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant outlet not found")
    return merchant


# ➕ 5. Add a Product to a Store's Menu
@router.post("/{merchant_id}/products", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def add_product_to_merchant(merchant_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """
    Add a food meal (e.g., Chips Choma) or a liquor item (e.g., Gin) to a specific store.
    """
    # Verify the store exists first
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant outlet not found")
        
    db_product = models.Product(
        merchant_id=merchant_id,
        name=product.name,
        description=product.description,
        price=product.price
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product