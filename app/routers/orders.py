import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.models import Order

router = APIRouter(prefix="/orders", tags=["orders"])


def serialize_order(order: Order) -> schemas.OrderOut:
    return schemas.OrderOut(
        id=order.id,
        orderCode=order.order_code,
        customer=schemas.Customer(
            customerId=order.customer_id,
            name=order.customer_name,
            phone=order.customer_phone,
            email=order.customer_email,
        ),
        items=[
            schemas.OrderItemOut(
                id=item.id,
                productId=item.product_id,
                productName=item.product_name,
                quantity=item.quantity,
                unitPrice=item.unit_price,
                totalPrice=item.total_price,
            )
            for item in order.items
        ],
        pricing=schemas.Pricing(
            subTotal=order.subtotal,
            shippingFee=order.shipping_fee,
            discount=order.discount,
            totalAmount=order.total_amount,
            currency=order.currency,
        ),
        shipping=schemas.Shipping(
            shippingOrderCode=order.shipping_order_code,
            status=order.shipping_status,
            address=schemas.Address(
                receiverName=order.receiver_name,
                receiverPhone=order.receiver_phone,
                fullAddress=order.receiver_address,
            ),
            shipper=schemas.Shipper(**order.shipper)
            if order.shipper
            else None,
            estimatedDeliveryTime=order.estimated_delivery_time,
            deliveredAt=order.delivered_at,
            failedReason=order.failed_reason,
        ),
        orderStatus=order.order_status,
        paymentMethod=order.payment_method,
        paymentStatus=order.payment_status,
        createdAt=order.created_at,
        updatedAt=order.updated_at,
    )


def serialize_order_status(order: Order) -> schemas.OrderStatusOut:
    return schemas.OrderStatusOut(
        orderCode=order.order_code,
        orderStatus=order.order_status,
        paymentStatus=order.payment_status,
        shippingStatus=order.shipping_status,
        shippingOrderCode=order.shipping_order_code,
        customer=schemas.Customer(
            customerId=order.customer_id,
            name=order.customer_name,
            phone=order.customer_phone,
            email=order.customer_email,
        ),
        pricing=schemas.Pricing(
            subTotal=order.subtotal,
            shippingFee=order.shipping_fee,
            discount=order.discount,
            totalAmount=order.total_amount,
            currency=order.currency,
        ),
        createdAt=order.created_at,
        updatedAt=order.updated_at,
    )


@router.post(
    "",
    response_model=schemas.OrderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    payload: schemas.OrderCreate, db: Session = Depends(get_db)
):
    existing = crud.get_order_by_code(db, payload.orderCode)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order code already exists.",
        )
    order = crud.create_order(db, payload)
    return serialize_order(order)


@router.get("", response_model=List[schemas.OrderOut])
def list_orders(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    orders = crud.get_orders(db, skip=skip, limit=limit)
    return [serialize_order(o) for o in orders]


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return serialize_order(order)


@router.get("/by-code/{order_code}", response_model=schemas.OrderOut)
def get_order_by_code(order_code: str, db: Session = Depends(get_db)):
    order = crud.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return serialize_order(order)


@router.get("/status/{order_code}", response_model=schemas.OrderStatusOut)
def get_order_status(order_code: str, db: Session = Depends(get_db)):
    """
    Lightweight endpoint for other systems to check current order status by orderCode.
    """
    order = crud.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return serialize_order_status(order)


@router.post("/status-update", response_model=schemas.OrderOut)
def external_status_update(
    payload: schemas.ExternalStatusUpdate, db: Session = Depends(get_db)
):
    """
    Endpoint for other systems to push status updates using orderId or orderCode.
    """
    order = None
    if payload.orderId is not None:
        order = crud.get_order(db, payload.orderId)
    elif payload.orderCode is not None:
        order = crud.get_order_by_code(db, payload.orderCode)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either orderId or orderCode is required.",
        )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Reuse internal update schema/logic
    update_payload = schemas.OrderUpdate(
        orderStatus=payload.orderStatus,
        paymentStatus=payload.paymentStatus,
        shippingStatus=payload.shippingStatus,
        shippingOrderCode=payload.shippingOrderCode,
        shipper=payload.shipper,
        estimatedDeliveryTime=payload.estimatedDeliveryTime,
        deliveredAt=payload.deliveredAt,
        failedReason=payload.failedReason,
    )
    updated = crud.update_order(db, order, update_payload)
    return serialize_order(updated)


@router.patch("/{order_id}", response_model=schemas.OrderOut)
def update_order(
    order_id: uuid.UUID, payload: schemas.OrderUpdate, db: Session = Depends(get_db)
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    updated = crud.update_order(db, order, payload)
    return serialize_order(updated)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    crud.delete_order(db, order)

