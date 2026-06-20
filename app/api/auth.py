from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.services import auth_utils

router = APIRouter(prefix="/api/auth", tags=["User Authentication"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: schemas.UserSignup, db: Session = Depends(get_db)):
    """
    Register a new customer profile.
    Automatically encrypts passwords and enforces uniform phone numbers.
    """
    # Force clean phone formatting
    phone = user_data.phone_number.strip()
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.phone_number == phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Hash the password securely before saving
    hashed_pwd = auth_utils.hash_password(user_data.password)

    new_user = models.User(
        full_name=user_data.full_name,
        phone_number=phone,
        hashed_password=hashed_pwd,
        role=models.UserRole.CUSTOMER
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "message": f"Account created successfully for {new_user.full_name}"}


@router.post("/login", response_model=schemas.TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Standard OAuth2 compatible login. 
    Accepts phone_number in the 'username' field and outputs a JWT token.
    """
    phone = form_data.username.strip()
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    user = db.query(models.User).filter(models.User.phone_number == phone).first()
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect phone number or password")

    # Generate the access token
    access_token = auth_utils.create_access_token(data={"sub": user.phone_number, "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }
