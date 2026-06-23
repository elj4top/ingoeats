from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME:             str   = "IngoEats API"
    SECRET_KEY:               str   = "change-this-in-production"
    ALGORITHM:                str   = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DATABASE_URL:             str   = "sqlite:///./ingoeats.db"

    # NEW — Paystack replaces all MPESA_* variables
    PAYSTACK_SECRET_KEY:      str   = ""
    PAYSTACK_PUBLIC_KEY:      str   = ""

    # Business rules
    DELIVERY_FEE:             float = 150.0
    PLATFORM_COMMISSION_RATE: float = 0.10
    RIDER_DELIVERY_SHARE:     float = 0.90

    CELERY_BROKER_URL:        str   = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND:    str   = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()