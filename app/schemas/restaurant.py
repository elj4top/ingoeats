from typing import List, Optional
from pydantic import BaseModel
from app.models.restaurant import MerchantType


class MerchantCreate(BaseModel):
    business_name: str
    merchant_type: MerchantType
    location:      str


# NEW — full onboarding form, includes bank details for Paystack subaccount
class MerchantOnboardRequest(BaseModel):
    business_name:  str
    bank_code:      str    # Paystack bank code e.g. "063" for Equity
    account_number: str
    merchant_type:  MerchantType
    location:       str


class ProductCreate(BaseModel):
    name:        str
    description: Optional[str] = None
    price:       float


class ProductResponse(BaseModel):
    id:           int
    merchant_id:  int
    name:         str
    description:  Optional[str]
    price:        float
    is_available: bool

    class Config:
        from_attributes = True


class MerchantResponse(BaseModel):
    id:                       int
    owner_id:                 Optional[int]
    business_name:            str
    merchant_type:            MerchantType
    location:                 str
    is_active:                bool
    paystack_subaccount_code: Optional[str]

    class Config:
        from_attributes = True


class MerchantDetailResponse(MerchantResponse):
    products: List[ProductResponse] = []