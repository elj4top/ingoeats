from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserOut, Token, RiderCreate
from app.core.security import hash_password, verify_password, create_access_token
from app.services.payment_service import register_rider_recipient

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone_number == data.phone_number).first():
        raise HTTPException(400, "Phone number already registered")
    user = User(
        full_name       = data.full_name,
        phone_number    = data.phone_number,
        email           = data.email,
        hashed_password = hash_password(data.password),
        role            = data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# NEW — rider registration also registers their M-Pesa with Paystack
@router.post("/register-rider", response_model=UserOut, status_code=201)
def register_rider(data: RiderCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone_number == data.phone_number).first():
        raise HTTPException(400, "Phone number already registered")

    recipient_code = None
    try:
        recipient_code = register_rider_recipient(data.full_name, data.phone_number)
    except ValueError:
        pass  # save user anyway, they can retry payout setup later

    user = User(
        full_name               = data.full_name,
        phone_number            = data.phone_number,
        email                   = data.email,
        hashed_password         = hash_password(data.password),
        role                    = UserRole.rider,
        paystack_recipient_code = recipient_code,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.phone_number == form_data.username) | (User.email == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token)