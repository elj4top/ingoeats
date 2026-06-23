from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create(db: Session, user_in: UserCreate) -> User:
    user = User(
        full_name       = user_in.full_name,
        email           = user_in.email,
        phone_number    = user_in.phone_number,
        hashed_password = hash_password(user_in.password),
        role            = user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user