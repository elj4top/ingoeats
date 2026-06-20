from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import mpesa, restaurants, orders # 1. Added orders here

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IngoEats API",
    description="Backend marketplace engine for Kakamega food, liquor, and last-mile Boda logistics.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(mpesa.router)
app.include_router(restaurants.router)
app.include_router(orders.router) # 2. Added order routing block here

@app.get("/")
def home():
    return {"status": "online", "marketplace": "IngoEats Kakamega"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

