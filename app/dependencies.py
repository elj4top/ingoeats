from sqlalchemy.orm import Session 
from app.db.database import SessionLocal

# Dependency to inject DB session into API routers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()