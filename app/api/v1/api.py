from fastapi import APIRouter

from app.api.v1.routes import auth, users, merchants, orders, drivers, payments

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(merchants.router)
api_router.include_router(orders.router)
api_router.include_router(drivers.router)
api_router.include_router(payments.router)
