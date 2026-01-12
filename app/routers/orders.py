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
            name=order.customer_name,
            phone=order.customer_phone,
            email=order.customer_email,
        ),
        items=[
            schemas.OrderItemOut(
                id=item.id,
                productId=item.product_id,
                productName=item.product.name if item.product else "Product not found",
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
            ) if order.receiver_name or order.receiver_phone or order.receiver_address else None,
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


@router.post(
    "",
    response_model=schemas.OrderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    payload: schemas.OrderCreate, db: Session = Depends(get_db)
):
    """
    Create order. Order code will be auto-generated.
    Products will be fetched from database using product_id from items.
    """
    order = crud.create_order(db, payload)
    return serialize_order(order)


@router.get("", response_model=List[schemas.OrderOut])
def list_orders(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    List orders with pagination.
    FastAPI automatically supports HEAD method for GET endpoints.
    """
    orders = crud.get_orders(db, skip=skip, limit=limit)
    return [serialize_order(o) for o in orders]


@router.get("/by-code/{order_code}", response_model=schemas.OrderOut)
def get_order_by_code(order_code: str, db: Session = Depends(get_db)):
    order = crud.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return serialize_order(order)


@router.post("/by-code/status-update/{order_code}", response_model=schemas.OrderOut)
def external_status_update(
    order_code: str,
    payload: schemas.ExternalStatusUpdate, 
    db: Session = Depends(get_db)
):
    """
    Endpoint for other systems to push status updates using orderCode.
    Only fields provided in the payload will be updated.
    order_code is required in the path, and status fields in the payload.
    """
    order = crud.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Only include fields that were actually provided (not None)
    # This ensures only the status fields sent will be updated
    update_data = payload.dict(exclude_none=True)
    update_payload = schemas.OrderUpdate(**update_data)
    
    updated = crud.update_order(db, order, update_payload)
    return serialize_order(updated)


@router.patch("/by-code/{order_code}", response_model=schemas.OrderOut)
def update_order(
    order_code: str, payload: schemas.OrderUpdate, db: Session = Depends(get_db)
):
    order = crud.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    updated = crud.update_order(db, order, payload)
    return serialize_order(updated)


@router.delete("/by-code/{order_code}", response_model=schemas.OrderOut)
def cancel_order(order_code: str, db: Session = Depends(get_db)):
    """
    Cancel order by setting status to CANCELLED (soft delete).
    Order is not actually deleted from database.
    """
    order = crud.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    cancelled_order = crud.cancel_order(db, order)
    return serialize_order(cancelled_order)

