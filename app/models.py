import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("order_code", name="uq_order_code"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_code: Mapped[str] = mapped_column(String(50), nullable=False)

    customer_id: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255))

    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_fee: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="VND")
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    payment_status: Mapped[str] = mapped_column(String(30), default="PENDING")

    shipping_order_code: Mapped[Optional[str]] = mapped_column(String(100))
    shipping_status: Mapped[str] = mapped_column(String(30), default="NOT_CREATED")
    receiver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    receiver_address: Mapped[str] = mapped_column(String(500), nullable=False)
    shipper: Mapped[Optional[dict]] = mapped_column(JSONB)
    estimated_delivery_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_reason: Mapped[Optional[str]] = mapped_column(String(500))

    order_status: Mapped[str] = mapped_column(String(30), default="CONFIRMED")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")

