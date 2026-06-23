# Project Structure

```text
app/
├── main.py                     # Entry point of FastAPI app

├── api/                        # HTTP layer (routes only)
│   └── v1/
│       └── routes/
│           ├── auth.py
│           ├── users.py
│           ├── restaurants.py
│           ├── orders.py
│           ├── drivers.py
│           └── payments.py

├── core/                       # Configuration & security
│   ├── config.py
│   └── security.py

├── models/                     # Database models (SQLAlchemy)
│   ├── user.py
│   ├── order.py
│   └── restaurant.py

├── schemas/                    # Request/Response validation (Pydantic)
│   ├── user.py
│   └── order.py

├── services/                   # Business logic layer
│   ├── user_service.py
│   ├── order_service.py
│   └── payment_service.py

├── repositories/               # Database queries layer (optional)
│   ├── user_repo.py
│   └── order_repo.py

├── db/                         # Database setup
│   ├── session.py
│   └── base.py

├── workers/                   # Background jobs
│   ├── celery_app.py
│   └── tasks.py

├── utils/                     # Helper functions
│   └── helpers.py

```

