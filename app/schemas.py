import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Customer(BaseModel):
    customerId: str = Field(..., max_length=50)
    name: str
    phone: str
    email: Optional[EmailStr] = None


class OrderItemCreate(BaseModel):
    productId: str
    productName: str
    quantity: int = Field(..., gt=0)
    unitPrice: float = Field(..., ge=0)
    totalPrice: float = Field(..., ge=0)


class Pricing(BaseModel):
    subTotal: float = Field(..., ge=0)
    shippingFee: float = Field(0, ge=0)
    discount: float = Field(0, ge=0)
    totalAmount: float = Field(..., ge=0)
    currency: str = "VND"


class Address(BaseModel):
    receiverName: str
    receiverPhone: str
    fullAddress: str


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
    address: Address
    shipper: Optional[Shipper] = None
    estimatedDeliveryTime: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    failedReason: Optional[str] = None


class OrderBase(BaseModel):
    orderCode: str
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


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    orderStatus: Optional[str] = None
    paymentStatus: Optional[str] = None
    shippingStatus: Optional[str] = Field(
        default=None,
        description="NOT_CREATED | CREATED | PICKED | DELIVERING | DELIVERED | FAILED | CANCELLED",
    )
    shippingOrderCode: Optional[str] = None
    shipper: Optional[Shipper] = None
    estimatedDeliveryTime: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    failedReason: Optional[str] = None


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


class OrderStatusOut(BaseModel):
    orderCode: str
    orderStatus: str
    paymentStatus: str
    shippingStatus: str
    shippingOrderCode: Optional[str] = None
    customer: Customer
    pricing: Pricing
    createdAt: datetime
    updatedAt: datetime


class ExternalStatusUpdate(BaseModel):
    """
    Payload for external systems to push status updates.
    At least one of orderId or orderCode should be provided.
    """

    orderId: Optional[uuid.UUID] = None
    orderCode: Optional[str] = None

    orderStatus: Optional[str] = None
    paymentStatus: Optional[str] = None
    shippingStatus: Optional[str] = None
    shippingOrderCode: Optional[str] = None
    shipper: Optional[Shipper] = None
    estimatedDeliveryTime: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    failedReason: Optional[str] = None

