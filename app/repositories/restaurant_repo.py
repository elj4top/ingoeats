from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.restaurant import Merchant, MerchantType, Product


def get_by_id(db: Session, merchant_id: int) -> Optional[Merchant]:
    return db.query(Merchant).filter(Merchant.id == merchant_id).first()


def get_by_owner(db: Session, owner_id: int) -> Optional[Merchant]:
    return db.query(Merchant).filter(Merchant.owner_id == owner_id).first()


def list_active(db: Session, merchant_type: Optional[MerchantType] = None) -> List[Merchant]:
    query = db.query(Merchant).filter(Merchant.is_active == True)  # noqa: E712
    if merchant_type is not None:
        query = query.filter(Merchant.merchant_type == merchant_type)
    return query.all()


def create(
    db: Session,
    owner_id: int,
    business_name: str,
    merchant_type: MerchantType,
    location: str,
    paystack_subaccount_code: Optional[str] = None,
) -> Merchant:
    merchant = Merchant(
        owner_id=owner_id,
        business_name=business_name,
        merchant_type=merchant_type,
        location=location,
        paystack_subaccount_code=paystack_subaccount_code,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def add_product(
    db: Session, merchant_id: int, name: str, description: Optional[str], price: float
) -> Product:
    product = Product(
        merchant_id=merchant_id, name=name, description=description, price=price
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_products(db: Session, merchant_id: int) -> List[Product]:
    return db.query(Product).filter(Product.merchant_id == merchant_id).all()


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()