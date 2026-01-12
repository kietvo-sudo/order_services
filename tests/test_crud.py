"""Unit tests for app.crud module"""
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app import crud, schemas
from app.constants import OrderStatus, PaymentMethod
from app.models import Order, OrderItem, Product


class TestGenerateOrderCode:
    """Tests for generate_order_code function"""
    
    def test_generate_order_code_format(self):
        """Test that order code follows expected format"""
        order_code = crud.generate_order_code()
        
        assert order_code.startswith("ORD-")
        parts = order_code.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 15  # YYYYMMDD-HHMMSS format
        assert len(parts[2]) == 4  # Random suffix
    
    def test_generate_order_code_uniqueness(self):
        """Test that generated order codes are unique"""
        codes = [crud.generate_order_code() for _ in range(10)]
        assert len(codes) == len(set(codes))
    
    def test_generate_order_code_contains_date(self):
        """Test that order code contains current date"""
        order_code = crud.generate_order_code()
        today = datetime.utcnow().strftime("%Y%m%d")
        assert today in order_code


class TestGenerateProductId:
    """Tests for generate_product_id function"""
    
    def test_generate_product_id_format(self):
        """Test that product ID is a valid UUID string"""
        product_id = crud.generate_product_id()
        
        # Should be a valid UUID string
        uuid.UUID(product_id)
        assert isinstance(product_id, str)
    
    def test_generate_product_id_uniqueness(self):
        """Test that generated product IDs are unique"""
        ids = [crud.generate_product_id() for _ in range(10)]
        assert len(ids) == len(set(ids))


class TestProductCRUD:
    """Tests for product CRUD operations"""
    
    def test_create_product_success(self, db_session):
        """Test successful product creation"""
        payload = schemas.ProductCreate(
            name="Test Product",
            description="Test Description",
            price=100.0,
            currency="VND",
            stock=50,
            status="ACTIVE",
        )
        
        product = crud.create_product(db_session, payload)
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.description == "Test Description"
        assert product.price == 100.0
        assert product.currency == "VND"
        assert product.stock == 50
        assert product.status == "ACTIVE"
        assert product.created_at is not None
    
    def test_create_product_with_minimal_fields(self, db_session):
        """Test product creation with minimal required fields"""
        payload = schemas.ProductCreate(
            name="Minimal Product",
            price=50.0,
        )
        
        product = crud.create_product(db_session, payload)
        
        assert product.name == "Minimal Product"
        assert product.price == 50.0
        assert product.currency == "VND"  # Default value
        assert product.stock == 0  # Default value
        assert product.status == "ACTIVE"  # Default value
    
    def test_create_product_database_error(self, db_session):
        """Test product creation with database error"""
        payload = schemas.ProductCreate(
            name="Test Product",
            price=100.0,
        )
        
        # Simulate database error
        db_session.commit = MagicMock(side_effect=Exception("Database error"))
        
        with pytest.raises(HTTPException) as exc_info:
            crud.create_product(db_session, payload)
        
        assert exc_info.value.status_code == 400
        assert "Failed to create product" in str(exc_info.value.detail)
    
    def test_get_product_success(self, db_session, sample_product):
        """Test successful product retrieval"""
        product = crud.get_product(db_session, sample_product.id)
        
        assert product is not None
        assert product.id == sample_product.id
        assert product.name == sample_product.name
    
    def test_get_product_not_found(self, db_session):
        """Test product retrieval when product doesn't exist"""
        product = crud.get_product(db_session, "non-existent-id")
        assert product is None
    
    def test_get_products_with_pagination(self, db_session):
        """Test product listing with pagination"""
        # Create multiple products
        for i in range(5):
            product = Product(
                id=str(uuid.uuid4()),
                name=f"Product {i}",
                price=100.0 + i,
                currency="VND",
                stock=10,
                status="ACTIVE",
            )
            db_session.add(product)
        db_session.commit()
        
        products = crud.get_products(db_session, skip=0, limit=3)
        assert len(products) == 3
        
        products = crud.get_products(db_session, skip=3, limit=3)
        assert len(products) == 2
    
    def test_update_product_success(self, db_session, sample_product):
        """Test successful product update"""
        updates = schemas.ProductUpdate(
            name="Updated Product",
            price=150.0,
            stock=75,
        )
        
        updated_product = crud.update_product(db_session, sample_product, updates)
        
        assert updated_product.name == "Updated Product"
        assert updated_product.price == 150.0
        assert updated_product.stock == 75
        assert updated_product.updated_at is not None
    
    def test_update_product_partial(self, db_session, sample_product):
        """Test partial product update"""
        original_name = sample_product.name
        updates = schemas.ProductUpdate(price=200.0)
        
        updated_product = crud.update_product(db_session, sample_product, updates)
        
        assert updated_product.name == original_name  # Unchanged
        assert updated_product.price == 200.0  # Updated
    
    def test_delete_product_success(self, db_session, sample_product):
        """Test successful product deletion"""
        product_id = sample_product.id
        crud.delete_product(db_session, sample_product)
        
        # Verify product is deleted
        deleted_product = db_session.query(Product).filter(Product.id == product_id).first()
        assert deleted_product is None


class TestOrderCRUD:
    """Tests for order CRUD operations"""
    
    def test_create_order_success(self, db_session, sample_product):
        """Test successful order creation"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
                email="customer@example.com",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=2,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {
                "shippingOrderCode": "SHIP-123",
                "status": "CREATED",
            }
            
            order = crud.create_order(db_session, payload)
            
            assert order.order_code is not None
            assert order.order_code.startswith("ORD-")
            assert order.customer_name == "Test Customer"
            assert order.customer_phone == "0123456789"
            assert order.customer_email == "customer@example.com"
            assert len(order.items) == 1
            assert order.items[0].quantity == 2
            assert order.items[0].unit_price == sample_product.price
            assert order.subtotal == sample_product.price * 2
            assert order.payment_method == PaymentMethod.COD
            assert order.order_status == OrderStatus.PENDING
            assert order.shipping_order_code == "SHIP-123"
            mock_shipment.assert_called_once()
    
    def test_create_order_product_not_found(self, db_session):
        """Test order creation with non-existent product"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId="non-existent-id",
                    quantity=1,
                )
            ],
        )
        
        with pytest.raises(HTTPException) as exc_info:
            crud.create_order(db_session, payload)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    def test_create_order_inactive_product(self, db_session):
        """Test order creation with inactive product"""
        inactive_product = Product(
            id=str(uuid.uuid4()),
            name="Inactive Product",
            price=100.0,
            currency="VND",
            stock=10,
            status="INACTIVE",
        )
        db_session.add(inactive_product)
        db_session.commit()
        
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=inactive_product.id,
                    quantity=1,
                )
            ],
        )
        
        with pytest.raises(HTTPException) as exc_info:
            crud.create_order(db_session, payload)
        
        assert exc_info.value.status_code == 400
        assert "not active" in str(exc_info.value.detail).lower()
    
    def test_create_order_multiple_items(self, db_session, sample_product):
        """Test order creation with multiple items"""
        product2 = Product(
            id=str(uuid.uuid4()),
            name="Product 2",
            price=200.0,
            currency="VND",
            stock=20,
            status="ACTIVE",
        )
        db_session.add(product2)
        db_session.commit()
        
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=2,
                ),
                schemas.OrderItemCreate(
                    productId=product2.id,
                    quantity=3,
                ),
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            order = crud.create_order(db_session, payload)
            
            assert len(order.items) == 2
            expected_subtotal = (sample_product.price * 2) + (product2.price * 3)
            assert order.subtotal == expected_subtotal
    
    def test_create_order_shipment_api_failure(self, db_session, sample_product):
        """Test order creation when shipment API fails"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = None  # API failure
            
            with pytest.raises(HTTPException) as exc_info:
                crud.create_order(db_session, payload)
            
            assert exc_info.value.status_code == 502
            assert "Failed to create shipment" in str(exc_info.value.detail)
            
            # Verify order was not saved to database
            orders = db_session.query(Order).all()
            assert len(orders) == 0
    
    def test_create_order_shipment_response_parsing(self, db_session, sample_product):
        """Test order creation with shipment API response parsing"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        future_time = datetime(2024, 12, 31, 12, 0, 0)
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {
                "shippingOrderCode": "SHIP-456",
                "status": "PICKED",
                "shipper": {"name": "Test Shipper", "phone": "0987654321"},
                "estimatedDeliveryTime": future_time.isoformat(),
                "orderStatus": "CONFIRMED",
            }
            
            order = crud.create_order(db_session, payload)
            
            assert order.shipping_order_code == "SHIP-456"
            assert order.shipping_status == "PICKED"
            assert order.shipper is not None
            assert order.order_status == "CONFIRMED"
    
    def test_get_order_by_code_success(self, db_session, sample_order):
        """Test successful order retrieval by code"""
        order = crud.get_order_by_code(db_session, sample_order.order_code)
        
        assert order is not None
        assert order.order_code == sample_order.order_code
        assert len(order.items) > 0
        # Verify eager loading of product relationship
        assert order.items[0].product is not None
    
    def test_get_order_by_code_not_found(self, db_session):
        """Test order retrieval when order doesn't exist"""
        order = crud.get_order_by_code(db_session, "ORD-NONEXISTENT")
        assert order is None
    
    def test_get_orders_with_pagination(self, db_session, sample_product):
        """Test order listing with pagination"""
        # Create multiple orders
        for i in range(5):
            order = Order(
                id=uuid.uuid4(),
                order_code=f"ORD-TEST-{i}",
                customer_id="",
                customer_name=f"Customer {i}",
                customer_phone="0123456789",
                subtotal=100.0,
                total_amount=100.0,
                currency="VND",
                payment_method="COD",
                payment_status="PENDING",
                shipping_status="NOT_CREATED",
                receiver_name=f"Customer {i}",
                receiver_phone="0123456789",
                receiver_address="Ho Chi Minh City",
                order_status="PENDING",
            )
            db_session.add(order)
        db_session.commit()
        
        orders = crud.get_orders(db_session, skip=0, limit=3)
        assert len(orders) == 3
        
        orders = crud.get_orders(db_session, skip=3, limit=3)
        assert len(orders) == 2
    
    def test_update_order_success(self, db_session, sample_order):
        """Test successful order update"""
        updates = schemas.OrderUpdate(orderStatus="CONFIRMED")
        
        updated_order = crud.update_order(db_session, sample_order, updates)
        
        assert updated_order.order_status == "CONFIRMED"
        assert updated_order.updated_at is not None
    
    def test_cancel_order_success(self, db_session, sample_order):
        """Test successful order cancellation"""
        cancelled_order = crud.cancel_order(db_session, sample_order)
        
        assert cancelled_order.order_status == "CANCELLED"
        assert cancelled_order.updated_at is not None
    
    def test_cancel_order_already_cancelled(self, db_session, sample_order):
        """Test cancelling an already cancelled order"""
        sample_order.order_status = "CANCELLED"
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            crud.cancel_order(db_session, sample_order)
        
        assert exc_info.value.status_code == 400
        assert "already cancelled" in str(exc_info.value.detail).lower()
    
    def test_create_order_calculates_subtotal(self, db_session, sample_product):
        """Test that order subtotal is calculated correctly"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=5,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            order = crud.create_order(db_session, payload)
            
            expected_subtotal = sample_product.price * 5
            assert order.subtotal == expected_subtotal
            assert order.items[0].total_price == expected_subtotal
    
    def test_create_order_default_values(self, db_session, sample_product):
        """Test that order has correct default values"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            order = crud.create_order(db_session, payload)
            
            assert order.shipping_fee == 0.0
            assert order.discount == 0.0
            assert order.currency == "VND"
            assert order.payment_status == "PENDING"
            assert order.shipping_status == "NOT_CREATED"
            assert order.customer_id == ""
            assert order.receiver_name == order.customer_name
            assert order.receiver_phone == order.customer_phone
    
    def test_create_order_unique_code_generation(self, db_session, sample_product):
        """Test that order code collision is handled"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            # Mock get_order_by_code to simulate collision on first call
            original_get_order = crud.get_order_by_code
            call_count = [0]
            
            def mock_get_order(db, code):
                call_count[0] += 1
                if call_count[0] == 1:
                    # Return existing order on first call (collision)
                    return MagicMock()
                # Return None on subsequent calls (no collision)
                return None
            
            with patch("app.crud.get_order_by_code", side_effect=mock_get_order):
                order = crud.create_order(db_session, payload)
                
                assert order.order_code is not None
                # Verify get_order_by_code was called multiple times due to collision
                assert call_count[0] > 1


class TestProductCRUDFailureScenarios:
    """Failure scenario tests for product CRUD operations"""
    
    def test_create_product_negative_price(self, db_session):
        """Test product creation with negative price - should be caught by Pydantic"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            payload = schemas.ProductCreate(
                name="Test Product",
                price=-100.0,  # Negative price
            )
    
    def test_create_product_negative_stock(self, db_session):
        """Test product creation with negative stock - should be caught by Pydantic"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            payload = schemas.ProductCreate(
                name="Test Product",
                price=100.0,
                stock=-10,  # Negative stock
            )
    
    def test_create_product_empty_name(self, db_session):
        """Test product creation with empty name"""
        payload = schemas.ProductCreate(
            name="",  # Empty name
            price=100.0,
        )
        
        # Should either fail validation or create with empty name
        # Depending on business logic, this might be allowed or rejected
        try:
            product = crud.create_product(db_session, payload)
            # If creation succeeds, verify it has empty name
            assert product.name == ""
        except (HTTPException, ValueError) as e:
            # If validation fails, that's also acceptable defensive behavior
            assert "name" in str(e).lower() or "empty" in str(e).lower()
    
    def test_create_product_very_large_price(self, db_session):
        """Test product creation with very large price value"""
        payload = schemas.ProductCreate(
            name="Expensive Product",
            price=1e15,  # Very large number
        )
        
        product = crud.create_product(db_session, payload)
        assert product.price == 1e15
    
    def test_create_product_very_large_stock(self, db_session):
        """Test product creation with very large stock value"""
        payload = schemas.ProductCreate(
            name="High Stock Product",
            price=100.0,
            stock=2147483647,  # Max int32 value
        )
        
        product = crud.create_product(db_session, payload)
        assert product.stock == 2147483647
    
    def test_create_product_invalid_status(self, db_session):
        """Test product creation with invalid status value"""
        payload = schemas.ProductCreate(
            name="Test Product",
            price=100.0,
            status="INVALID_STATUS",  # Not ACTIVE or INACTIVE
        )
        
        # Should create successfully (status is just a string field)
        # But defensive behavior might validate it
        product = crud.create_product(db_session, payload)
        assert product.status == "INVALID_STATUS"
    
    def test_update_product_none_product(self, db_session):
        """Test updating None product object"""
        updates = schemas.ProductUpdate(name="Updated")
        
        with pytest.raises((AttributeError, TypeError)):
            crud.update_product(db_session, None, updates)
    
    def test_update_product_negative_price(self, db_session, sample_product):
        """Test product update with negative price - should be caught by Pydantic"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            updates = schemas.ProductUpdate(price=-50.0)
    
    def test_update_product_negative_stock(self, db_session, sample_product):
        """Test product update with negative stock - should be caught by Pydantic"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            updates = schemas.ProductUpdate(stock=-5)
    
    def test_update_product_empty_name(self, db_session, sample_product):
        """Test product update with empty name"""
        updates = schemas.ProductUpdate(name="")
        
        updated_product = crud.update_product(db_session, sample_product, updates)
        assert updated_product.name == ""
    
    def test_update_product_very_large_values(self, db_session, sample_product):
        """Test product update with very large numeric values"""
        updates = schemas.ProductUpdate(
            price=1e15,
            stock=2147483647,
        )
        
        updated_product = crud.update_product(db_session, sample_product, updates)
        assert updated_product.price == 1e15
        assert updated_product.stock == 2147483647
    
    def test_delete_product_none_product(self, db_session):
        """Test deleting None product object"""
        with pytest.raises((AttributeError, TypeError)):
            crud.delete_product(db_session, None)


class TestOrderCRUDFailureScenarios:
    """Failure scenario tests for order CRUD operations"""
    
    def test_create_order_empty_items_list(self, db_session, sample_product):
        """Test order creation with empty items list"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[],  # Empty items list
        )
        
        # Current implementation may allow empty items or fail
        # Test defensive behavior - should handle gracefully
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            # Empty items might cause issues in shipment API or be allowed
            # Test both scenarios
            try:
                order = crud.create_order(db_session, payload)
                # If creation succeeds, verify it has empty items
                assert len(order.items) == 0
            except HTTPException as exc_info:
                # If validation fails, verify error message
                assert exc_info.status_code >= 400
                error_detail = str(exc_info.detail).lower()
                # Error should indicate problem with items or shipment
                assert "item" in error_detail or "shipment" in error_detail or "empty" in error_detail
    
    def test_create_order_negative_quantity(self, db_session, sample_product):
        """Test order creation with negative quantity - should be caught by Pydantic"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            payload = schemas.OrderCreate(
                customer=schemas.Customer(
                    name="Test Customer",
                    phone="0123456789",
                ),
                items=[
                    schemas.OrderItemCreate(
                        productId=sample_product.id,
                        quantity=-1,  # Negative quantity
                    )
                ],
            )
    
    def test_create_order_zero_quantity(self, db_session, sample_product):
        """Test order creation with zero quantity - should be caught by Pydantic"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            payload = schemas.OrderCreate(
                customer=schemas.Customer(
                    name="Test Customer",
                    phone="0123456789",
                ),
                items=[
                    schemas.OrderItemCreate(
                        productId=sample_product.id,
                        quantity=0,  # Zero quantity (gt=0 validation)
                    )
                ],
            )
    
    def test_create_order_very_large_quantity(self, db_session, sample_product):
        """Test order creation with very large quantity"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=2147483647,  # Max int32 value
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            order = crud.create_order(db_session, payload)
            assert order.items[0].quantity == 2147483647
    
    def test_create_order_empty_customer_name(self, db_session, sample_product):
        """Test order creation with empty customer name"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="",  # Empty name
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            # Should either create successfully or fail validation
            try:
                order = crud.create_order(db_session, payload)
                assert order.customer_name == ""
            except (HTTPException, ValueError) as e:
                assert "name" in str(e).lower() or "customer" in str(e).lower()
    
    def test_create_order_empty_customer_phone(self, db_session, sample_product):
        """Test order creation with empty customer phone"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="",  # Empty phone
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            # Should either create successfully or fail validation
            try:
                order = crud.create_order(db_session, payload)
                assert order.customer_phone == ""
            except (HTTPException, ValueError) as e:
                assert "phone" in str(e).lower() or "customer" in str(e).lower()
    
    def test_create_order_invalid_email_format(self, db_session, sample_product):
        """Test order creation with invalid email format - should be caught by Pydantic"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            payload = schemas.OrderCreate(
                customer=schemas.Customer(
                    name="Test Customer",
                    phone="0123456789",
                    email="invalid-email",  # Invalid email format
                ),
                items=[
                    schemas.OrderItemCreate(
                        productId=sample_product.id,
                        quantity=1,
                    )
                ],
            )
    
    def test_create_order_duplicate_product_ids(self, db_session, sample_product):
        """Test order creation with duplicate product IDs in items"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                ),
                schemas.OrderItemCreate(
                    productId=sample_product.id,  # Same product ID
                    quantity=2,
                ),
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            # Should create successfully (duplicate products allowed)
            order = crud.create_order(db_session, payload)
            assert len(order.items) == 2
            assert all(item.product_id == sample_product.id for item in order.items)
    
    def test_create_order_out_of_stock(self, db_session, sample_product):
        """Test order creation when product is out of stock"""
        # Set product stock to 0
        sample_product.stock = 0
        db_session.commit()
        
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            # Current implementation doesn't check stock, so it should succeed
            # But this tests defensive behavior - should either check stock or allow it
            order = crud.create_order(db_session, payload)
            assert order is not None
    
    def test_create_order_insufficient_stock(self, db_session, sample_product):
        """Test order creation when quantity exceeds available stock"""
        # Set product stock to 5
        sample_product.stock = 5
        db_session.commit()
        
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=10,  # More than available stock
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.return_value = {"status": "CREATED"}
            
            # Current implementation doesn't check stock, so it should succeed
            # But this tests defensive behavior
            order = crud.create_order(db_session, payload)
            assert order is not None
    
    def test_create_order_shipment_api_exception_during_call(self, db_session, sample_product):
        """Test order creation when shipment API raises exception during call"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            mock_shipment.side_effect = Exception("Unexpected API error")
            
            with pytest.raises(HTTPException) as exc_info:
                crud.create_order(db_session, payload)
            
            assert exc_info.value.status_code == 502
            assert "Failed to create shipment" in str(exc_info.value.detail)
    
    def test_create_order_invalid_datetime_parsing(self, db_session, sample_product):
        """Test order creation with invalid datetime in shipment response"""
        payload = schemas.OrderCreate(
            customer=schemas.Customer(
                name="Test Customer",
                phone="0123456789",
            ),
            items=[
                schemas.OrderItemCreate(
                    productId=sample_product.id,
                    quantity=1,
                )
            ],
        )
        
        with patch("app.services.send_order_to_shipment") as mock_shipment:
            # Return invalid datetime format
            mock_shipment.return_value = {
                "shippingOrderCode": "SHIP-123",
                "status": "CREATED",
                "estimatedDeliveryTime": "invalid-datetime-format",  # Invalid format
            }
            
            # Should handle gracefully (log warning and continue)
            order = crud.create_order(db_session, payload)
            assert order is not None
            # estimated_delivery_time should be None if parsing fails
            assert order.estimated_delivery_time is None
    
    def test_update_order_none_order(self, db_session):
        """Test updating None order object"""
        updates = schemas.OrderUpdate(orderStatus="CONFIRMED")
        
        with pytest.raises((AttributeError, TypeError)):
            crud.update_order(db_session, None, updates)
    
    def test_update_order_invalid_status(self, db_session, sample_order):
        """Test order update with invalid orderStatus value"""
        updates = schemas.OrderUpdate(orderStatus="INVALID_STATUS")
        
        # Should update successfully (status is just a string field)
        # But defensive behavior might validate it
        updated_order = crud.update_order(db_session, sample_order, updates)
        assert updated_order.order_status == "INVALID_STATUS"
    
    def test_update_order_empty_status(self, db_session, sample_order):
        """Test order update with empty orderStatus"""
        updates = schemas.OrderUpdate(orderStatus="")
        
        updated_order = crud.update_order(db_session, sample_order, updates)
        assert updated_order.order_status == ""
    
    def test_cancel_order_none_order(self, db_session):
        """Test cancelling None order object"""
        with pytest.raises((AttributeError, TypeError)):
            crud.cancel_order(db_session, None)
    
    def test_cancel_order_already_delivered(self, db_session, sample_order):
        """Test cancelling an already delivered order"""
        sample_order.order_status = "DELIVERED"
        db_session.commit()
        
        # Should either allow cancellation or raise error
        try:
            cancelled_order = crud.cancel_order(db_session, sample_order)
            assert cancelled_order.order_status == "CANCELLED"
        except HTTPException as e:
            # If cancellation is not allowed for delivered orders
            assert e.status_code == 400
            assert "delivered" in str(e.detail).lower() or "cannot" in str(e.detail).lower()
    
    def test_cancel_order_already_completed(self, db_session, sample_order):
        """Test cancelling an already completed order"""
        sample_order.order_status = "COMPLETED"
        db_session.commit()
        
        # Should either allow cancellation or raise error
        try:
            cancelled_order = crud.cancel_order(db_session, sample_order)
            assert cancelled_order.order_status == "CANCELLED"
        except HTTPException as e:
            # If cancellation is not allowed for completed orders
            assert e.status_code == 400
            assert "completed" in str(e.detail).lower() or "cannot" in str(e.detail).lower()
    
    def test_get_order_by_code_empty_string(self, db_session):
        """Test getting order with empty order code"""
        order = crud.get_order_by_code(db_session, "")
        assert order is None
    
    def test_get_order_by_code_very_long_string(self, db_session):
        """Test getting order with very long order code"""
        long_code = "ORD-" + "A" * 1000
        order = crud.get_order_by_code(db_session, long_code)
        assert order is None
    
    def test_get_product_invalid_id_format(self, db_session):
        """Test getting product with invalid ID format"""
        # Try with various invalid formats
        invalid_ids = ["", "   ", "non-existent-id-with-special-chars-!@#$"]
        
        for invalid_id in invalid_ids:
            product = crud.get_product(db_session, invalid_id)
            assert product is None
    
    def test_get_products_negative_skip(self, db_session):
        """Test getting products with negative skip value"""
        products = crud.get_products(db_session, skip=-10, limit=10)
        # Should handle gracefully (SQLAlchemy offset handles negative)
        assert isinstance(products, list)
    
    def test_get_products_negative_limit(self, db_session):
        """Test getting products with negative limit value"""
        products = crud.get_products(db_session, skip=0, limit=-10)
        # Should handle gracefully (SQLAlchemy limit handles negative)
        assert isinstance(products, list)
    
    def test_get_orders_negative_skip(self, db_session):
        """Test getting orders with negative skip value"""
        orders = crud.get_orders(db_session, skip=-10, limit=10)
        # Should handle gracefully
        assert isinstance(orders, list)
    
    def test_get_orders_negative_limit(self, db_session):
        """Test getting orders with negative limit value"""
        orders = crud.get_orders(db_session, skip=0, limit=-10)
        # Should handle gracefully
        assert isinstance(orders, list)

