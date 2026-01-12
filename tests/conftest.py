"""Pytest configuration and shared fixtures"""
import uuid
from datetime import datetime
from typing import Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Order, OrderItem, Product


# In-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_product(db_session: Session) -> Product:
    """Create a sample product for testing"""
    product = Product(
        id=str(uuid.uuid4()),
        name="Test Product",
        description="Test Description",
        price=100.0,
        currency="VND",
        stock=100,
        status="ACTIVE",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_order(db_session: Session, sample_product: Product) -> Order:
    """Create a sample order for testing"""
    order = Order(
        id=uuid.uuid4(),
        order_code="ORD-20240101-120000-1234",
        customer_id="customer-123",
        customer_name="Test Customer",
        customer_phone="0123456789",
        customer_email="test@example.com",
        subtotal=200.0,
        shipping_fee=10.0,
        discount=0.0,
        total_amount=210.0,
        currency="VND",
        payment_method="COD",
        payment_status="PENDING",
        shipping_status="NOT_CREATED",
        receiver_name="Test Customer",
        receiver_phone="0123456789",
        receiver_address="Ho Chi Minh City, Vietnam",
        order_status="PENDING",
    )
    
    order_item = OrderItem(
        order_id=order.id,
        product_id=sample_product.id,
        quantity=2,
        unit_price=100.0,
        total_price=200.0,
    )
    order_item.product = sample_product
    order.items = [order_item]
    
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for external API calls"""
    return MagicMock()

