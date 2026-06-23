from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import every model here so Base.metadata is aware of all tables.
# This is also where Alembic would look if migrations are added later.
from app.models.user import User  
from app.models.restaurant import Merchant, Product 
from app.models.order import Order, OrderItem, DeliveryPayment 
