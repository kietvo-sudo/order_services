from fastapi import FastAPI

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import orders

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
def startup():
    # Ensure tables exist; in production prefer migrations.
    Base.metadata.create_all(bind=engine)


app.include_router(orders.router)