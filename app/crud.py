import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app import schemas
from app.constants import OrderStatus, PaymentMethod
from app.models import Order, OrderItem, Product


def generate_order_code() -> str:
    """Generate order code in format: ORD-YYYYMMDD-HHMMSS-XXXX"""
    now = datetime.utcnow()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    random_suffix = str(uuid.uuid4().int)[:4]
    return f"ORD-{timestamp}-{random_suffix}"


def generate_product_id() -> str:
    """Generate product ID using UUID"""
    return str(uuid.uuid4())


# Product CRUD functions
def create_product(db: Session, payload: schemas.ProductCreate) -> Product:
    # Auto-generate product ID
    product_id = generate_product_id()
    
    # Ensure unique ID (regenerate if collision)
    existing = get_product(db, product_id)
    while existing:
        product_id = generate_product_id()
        existing = get_product(db, product_id)
    
    try:
        product = Product(
            id=product_id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            currency=payload.currency,
            stock=payload.stock,
            status=payload.status,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create product: {str(e)}",
        )


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return (
        db.query(Product)
        .order_by(Product.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_product(db: Session, product_id: str) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def update_product(
    db: Session, product: Product, updates: schemas.ProductUpdate
) -> Product:
    if updates.name is not None:
        product.name = updates.name
    if updates.description is not None:
        product.description = updates.description
    if updates.price is not None:
        product.price = updates.price
    if updates.currency is not None:
        product.currency = updates.currency
    if updates.stock is not None:
        product.stock = updates.stock
    if updates.status is not None:
        product.status = updates.status
    
    product.updated_at = datetime.utcnow()
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()


# Order CRUD functions
def create_order(db: Session, payload: schemas.OrderCreate) -> Order:
    customer = payload.customer

    # Auto-generate order code
    order_code = generate_order_code()
    
    # Ensure unique order code (regenerate if collision)
    existing_order = get_order_by_code(db, order_code)
    while existing_order:
        order_code = generate_order_code()
        existing_order = get_order_by_code(db, order_code)

    # Fetch products and build order items
    order_items = []
    calculated_subtotal = 0.0
    
    for item in payload.items:
        product = get_product(db, item.productId)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.productId} not found.",
            )
        if product.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item.productId} is not active.",
            )
        
        unit_price = product.price
        total_price = unit_price * item.quantity
        calculated_subtotal += total_price
        
        order_item = OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        # Set product relationship explicitly for shipment API
        order_item.product = product
        order_items.append(order_item)

    # Set default payment method to COD (Cash on Delivery)
    payment_method_id = PaymentMethod.COD

    # Set default values for other fields
    shipping_fee = 0.0
    discount = 0.0
    final_total = calculated_subtotal + shipping_fee - discount
    currency = "VND"
    payment_status = "PENDING"
    order_status = OrderStatus.PENDING

    # Create order with minimal required data
    # Use customer information as default for receiver information
    # customer_id is not provided by user, set to empty string
    order = Order(
        order_code=order_code,
        customer_id="",  # Empty string as default since customer_id is not provided
        customer_name=customer.name,
        customer_phone=customer.phone,
        customer_email=customer.email,
        subtotal=calculated_subtotal,
        shipping_fee=shipping_fee,
        discount=discount,
        total_amount=final_total,
        currency=currency,
        payment_method=payment_method_id,
        payment_status=payment_status,
        shipping_order_code=None,
        shipping_status="NOT_CREATED",
        # Use customer information as default for receiver
        receiver_name=customer.name,
        receiver_phone=customer.phone,
        receiver_address="Ho Chi Minh City, Vietnam",  # Default address for shipment API validation
        shipper=None,
        estimated_delivery_time=None,
        delivered_at=None,
        failed_reason=None,
        order_status=order_status,
    )

    order.items = order_items

    # Send order data to shipment API BEFORE saving to database
    # Only save to database after receiving successful response
    from app.services import send_order_to_shipment
    import logging
    logger = logging.getLogger(__name__)
    
    shipment_response = send_order_to_shipment(order)
    
    if shipment_response is None:
        # Shipment API failed - raise error and don't save to database
        logger.error(f"Failed to send order {order.order_code} to shipment API. Order not saved.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create shipment. Order was not created. Please try again.",
        )
    
    # Update order with shipment API response data
    if isinstance(shipment_response, dict):
        # Extract shipping information from shipment API response
        if "shippingOrderCode" in shipment_response and shipment_response["shippingOrderCode"]:
            order.shipping_order_code = shipment_response["shippingOrderCode"]
        if "status" in shipment_response and shipment_response["status"]:
            order.shipping_status = shipment_response["status"]
        if "shipper" in shipment_response and shipment_response["shipper"]:
            order.shipper = shipment_response["shipper"]
        if "estimatedDeliveryTime" in shipment_response and shipment_response["estimatedDeliveryTime"]:
            from datetime import datetime
            try:
                # Parse ISO format datetime string
                order.estimated_delivery_time = datetime.fromisoformat(
                    shipment_response["estimatedDeliveryTime"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse estimatedDeliveryTime: {e}")
        if "orderStatus" in shipment_response and shipment_response["orderStatus"]:
            order.order_status = shipment_response["orderStatus"]
        # Do NOT update paymentMethod from shipment API - keep our randomly selected value
        logger.info(f"Updated order {order.order_code} with shipment API response data")
        logger.debug(f"Payment method remains: {order.payment_method}")
    
    # Shipment API succeeded - now save to database
    db.add(order)
    db.commit()
    db.refresh(order)
    # Eager load product relationship
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )
    
    logger.info(f"Order {order.order_code} created successfully after shipment API confirmation")
    
    return order


def get_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .order_by(Order.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_order_by_code(db: Session, order_code: str) -> Optional[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.order_code == order_code)
        .first()
    )


def update_order(
    db: Session, order: Order, updates: schemas.OrderUpdate
) -> Order:
    """
    Update order - only orderStatus can be updated.
    If current status is PENDING and new status is CANCELLED,
    call external shipment API before updating database.
    """
    import logging
    from app.services import update_shipment_status
    from app.constants import OrderStatus
    
    logger = logging.getLogger(__name__)
    
    # Check if we need to call external API before updating
    current_status = order.order_status
    new_status = updates.orderStatus
    
    # Normalize status values for comparison (case-insensitive)
    current_status_upper = current_status.upper() if current_status else ""
    new_status_upper = new_status.upper() if new_status else ""
    
    # If current status is PENDING and new status is CANCELLED, call external API first
    if current_status_upper == OrderStatus.PENDING and new_status_upper == OrderStatus.CANCELLED:
        logger.info(
            f"Order {order.order_code} is being cancelled from PENDING status. "
            f"Calling external shipment API before updating database."
        )
        
        # Call external API before making any database changes
        api_success = update_shipment_status(order.order_code, new_status)
        
        if not api_success:
            # External API call failed - raise error and don't update database
            logger.error(
                f"Failed to update shipment status for order {order.order_code} via external API. "
                f"Order status not updated in database."
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to cancel shipment. Order status was not updated. Please try again.",
            )
        
        logger.info(
            f"Successfully updated shipment status for order {order.order_code} via external API. "
            f"Proceeding with database update."
        )
    
    # Update order status
    order.order_status = updates.orderStatus

    order.updated_at = datetime.utcnow()
    db.add(order)
    db.commit()
    # Eager load product relationship
    db.refresh(order)
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )
    return order


def cancel_order(db: Session, order: Order) -> Order:
    """Soft delete: set order status to CANCELLED"""
    if order.order_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already cancelled.",
        )
    order.order_status = "CANCELLED"
    order.updated_at = datetime.utcnow()
    db.add(order)
    db.commit()
    # Eager load product relationship
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )
    return order

