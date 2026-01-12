import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import orders, products

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
# Log CORS configuration for debugging
logger.info(f"CORS Configuration: origins={settings.cors_origins}, credentials={settings.cors_allow_credentials}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.on_event("startup")
def startup():
    # Ensure tables exist; in production prefer migrations.
    Base.metadata.create_all(bind=engine)


app.include_router(orders.router)
app.include_router(products.router)