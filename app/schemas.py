import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    currency: str = "VND"
    stock: int = Field(default=0, ge=0)
    status: str = Field(default="ACTIVE", description="ACTIVE | INACTIVE")


class ProductCreate(ProductBase):
    pass  # orderCode will be auto-generated


class ProductOut(ProductBase):
    id: str
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")

    class Config:
        from_attributes = True
        populate_by_name = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, description="ACTIVE | INACTIVE")


class Customer(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None


class OrderItemCreate(BaseModel):
    productId: str
    quantity: int = Field(..., gt=0)


class Pricing(BaseModel):
    subTotal: float = Field(..., ge=0)
    shippingFee: float = Field(0, ge=0)
    discount: float = Field(0, ge=0)
    totalAmount: float = Field(..., ge=0)
    currency: str = "VND"


class Address(BaseModel):
    receiverName: Optional[str] = None
    receiverPhone: Optional[str] = None
    fullAddress: Optional[str] = None


class Shipper(BaseModel):
    shipperId: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    vehicleType: Optional[str] = Field(
        default=None, description="motorbike | car | truck"
    )


class Shipping(BaseModel):
    shippingOrderCode: Optional[str] = None
    status: str = Field(
        default="NOT_CREATED",
        description="NOT_CREATED | CREATED | PICKED | DELIVERING | DELIVERED | FAILED | CANCELLED",
    )
    address: Optional[Address] = None
    shipper: Optional[Shipper] = None
    estimatedDeliveryTime: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    failedReason: Optional[str] = None


class OrderBase(BaseModel):
    customer: Customer
    items: List[OrderItemCreate]
    pricing: Pricing
    shipping: Shipping
    orderStatus: str = Field(
        default="CONFIRMED",
        description="DRAFT | CONFIRMED | CANCELLED | COMPLETED",
    )
    paymentMethod: Optional[str] = None
    paymentStatus: str = "PENDING"


class OrderCreate(BaseModel):
    """Create order with only customer and items. Other fields will be auto-generated."""
    customer: Customer
    items: List[OrderItemCreate]
    # orderCode will be auto-generated
    # pricing, shipping, orderStatus, paymentMethod, paymentStatus will be auto-generated


class OrderUpdate(BaseModel):
    """Update order - only orderStatus can be updated."""
    orderStatus: str


class OrderItemOut(BaseModel):
    id: int
    productId: str
    productName: str
    quantity: int
    unitPrice: float
    totalPrice: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: uuid.UUID
    orderCode: str
    customer: Customer
    items: List[OrderItemOut]
    pricing: Pricing
    shipping: Shipping
    orderStatus: str
    paymentMethod: Optional[str]
    paymentStatus: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class ExternalStatusUpdate(BaseModel):
    """
    Payload for external systems to push status updates.
    order_code is provided in the API path.
    All status fields are optional, but at least one should be provided.
    """

    orderStatus: Optional[str] = None
    paymentStatus: Optional[str] = None
    shippingStatus: Optional[str] = None
    shippingOrderCode: Optional[str] = None
    shipper: Optional[Shipper] = None
    estimatedDeliveryTime: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    failedReason: Optional[str] = None

