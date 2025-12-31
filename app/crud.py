import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app import schemas
from app.models import Order, OrderItem


def create_order(db: Session, payload: schemas.OrderCreate) -> Order:
    customer = payload.customer
    pricing = payload.pricing
    shipping = payload.shipping

    order = Order(
        order_code=payload.orderCode,
        customer_id=customer.customerId,
        customer_name=customer.name,
        customer_phone=customer.phone,
        customer_email=customer.email,
        subtotal=pricing.subTotal,
        shipping_fee=pricing.shippingFee,
        discount=pricing.discount,
        total_amount=pricing.totalAmount,
        currency=pricing.currency,
        payment_method=payload.paymentMethod,
        payment_status=payload.paymentStatus,
        shipping_order_code=shipping.shippingOrderCode,
        shipping_status=shipping.status,
        receiver_name=shipping.address.receiverName,
        receiver_phone=shipping.address.receiverPhone,
        receiver_address=shipping.address.fullAddress,
        shipper=shipping.shipper.dict() if shipping.shipper else None,
        estimated_delivery_time=shipping.estimatedDeliveryTime,
        delivered_at=shipping.deliveredAt,
        failed_reason=shipping.failedReason,
        order_status=payload.orderStatus,
    )

    order.items = [
        OrderItem(
            product_id=item.productId,
            product_name=item.productName,
            quantity=item.quantity,
            unit_price=item.unitPrice,
            total_price=item.totalPrice,
        )
        for item in payload.items
    ]

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    return (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_order(db: Session, order_id: uuid.UUID) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_by_code(db: Session, order_code: str) -> Optional[Order]:
    return db.query(Order).filter(Order.order_code == order_code).first()


def update_order(
    db: Session, order: Order, updates: schemas.OrderUpdate
) -> Order:
    if updates.orderStatus is not None:
        order.order_status = updates.orderStatus
    if updates.paymentStatus is not None:
        order.payment_status = updates.paymentStatus
    if updates.shippingStatus is not None:
        order.shipping_status = updates.shippingStatus
    if updates.shippingOrderCode is not None:
        order.shipping_order_code = updates.shippingOrderCode
    if updates.shipper is not None:
        order.shipper = updates.shipper.dict() if updates.shipper else None
    if updates.estimatedDeliveryTime is not None:
        order.estimated_delivery_time = updates.estimatedDeliveryTime
    if updates.deliveredAt is not None:
        order.delivered_at = updates.deliveredAt
    if updates.failedReason is not None:
        order.failed_reason = updates.failedReason

    order.updated_at = datetime.utcnow()
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order: Order) -> None:
    db.delete(order)
    db.commit()

