# Order Services API Documentation

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication and Authorization](#authentication-and-authorization)
3. [Base URL](#base-url)
4. [Orders API](#orders-api)
5. [Products API](#products-api)
6. [Data Models](#data-models)
7. [Error Responses](#error-responses)

---

## API Overview

The Order Services API is a RESTful API built with FastAPI that provides comprehensive order and product management functionality. The API enables:

- **Order Management**: Create, retrieve, update, and cancel orders with full customer, shipping, and payment information
- **Product Management**: Manage product catalog with CRUD operations
- **External Integration**: Supports status updates from external systems (e.g., shipment services)
- **Order Tracking**: Track orders by unique order codes with detailed status information

### Key Features
- Automatic order code generation (`ORD-YYYYMMDD-HHMMSS-XXXX` format)
- Integration with external shipment API for order fulfillment
- Support for multiple payment methods and shipping statuses
- Comprehensive order status tracking (DRAFT, CONFIRMED, CANCELLED, COMPLETED)
- Product inventory management with stock tracking

---

## Authentication and Authorization

**Current Status**: The API does not implement authentication or authorization mechanisms. All endpoints are publicly accessible.

**Note**: For production deployments, it is recommended to implement:
- API key authentication
- JWT token-based authentication
- Role-based access control (RBAC)

---

## Base URL

```
http://localhost:8000
```

The API provides interactive documentation at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

---

## Orders API

### Create Order

Creates a new order with customer and item information. The order code is automatically generated, and pricing is calculated based on product prices. The order is automatically sent to the shipment API before being saved to the database.

**Endpoint**: `POST /orders`

**Request Body**:
```json
{
  "customer": {
    "name": "string",
    "phone": "string",
    "email": "string (optional, must be valid email)"
  },
  "items": [
    {
      "productId": "string",
      "quantity": "integer (must be > 0)"
    }
  ]
}
```

**Request Schema**: `OrderCreate`
- `customer` (required): Customer information object
  - `name` (required, string): Customer name
  - `phone` (required, string): Customer phone number
  - `email` (optional, EmailStr): Customer email address
- `items` (required, array): List of order items
  - `productId` (required, string): Product ID (must exist and be ACTIVE)
  - `quantity` (required, integer, > 0): Quantity of the product

**Response**: `201 Created`

**Response Body**: `OrderOut` (see [Data Models](#data-models))

**Status Codes**:
- `201 Created`: Order created successfully
- `400 Bad Request`: Invalid request data or product not active
- `404 Not Found`: Product ID not found
- `502 Bad Gateway`: Failed to create shipment (order not saved)

**Example Request**:
```json
{
  "customer": {
    "name": "John Doe",
    "phone": "+84123456789",
    "email": "john.doe@example.com"
  },
  "items": [
    {
      "productId": "550e8400-e29b-41d4-a716-446655440000",
      "quantity": 2
    }
  ]
}
```

**Example Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "orderCode": "ORD-20240101-120000-1234",
  "customer": {
    "name": "John Doe",
    "phone": "+84123456789",
    "email": "john.doe@example.com"
  },
  "items": [
    {
      "id": 1,
      "productId": "550e8400-e29b-41d4-a716-446655440000",
      "productName": "Product Name",
      "quantity": 2,
      "unitPrice": 100000.0,
      "totalPrice": 200000.0
    }
  ],
  "pricing": {
    "subTotal": 200000.0,
    "shippingFee": 0.0,
    "discount": 0.0,
    "totalAmount": 200000.0,
    "currency": "VND"
  },
  "shipping": {
    "shippingOrderCode": "SHIP-12345",
    "status": "CREATED",
    "address": {
      "receiverName": "John Doe",
      "receiverPhone": "+84123456789",
      "fullAddress": "Ho Chi Minh City, Vietnam"
    },
    "shipper": null,
    "estimatedDeliveryTime": "2024-01-02T12:00:00Z",
    "deliveredAt": null,
    "failedReason": null
  },
  "orderStatus": "PENDING",
  "paymentMethod": "COD",
  "paymentStatus": "PENDING",
  "createdAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z"
}
```

**Notes**:
- Order code is auto-generated in format: `ORD-YYYYMMDD-HHMMSS-XXXX`
- Pricing (subtotal, shipping fee, discount, total) is auto-calculated
- Default payment method is `COD` (Cash on Delivery)
- Default order status is `PENDING`
- Order is sent to shipment API before database save; if shipment API fails, order is not created
- Default shipping address is "Ho Chi Minh City, Vietnam" if not provided

---

### List Orders

Retrieves a paginated list of orders, ordered by most recently updated first.

**Endpoint**: `GET /orders`

**Query Parameters**:
- `skip` (optional, integer, default: 0): Number of records to skip (for pagination)
- `limit` (optional, integer, default: 50): Maximum number of records to return

**Response**: `200 OK`

**Response Body**: Array of `OrderOut` objects

**Status Codes**:
- `200 OK`: Successfully retrieved orders

**Example Request**:
```
GET /orders?skip=0&limit=10
```

**Example Response**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "orderCode": "ORD-20240101-120000-1234",
    "customer": { ... },
    "items": [ ... ],
    "pricing": { ... },
    "shipping": { ... },
    "orderStatus": "PENDING",
    "paymentMethod": "COD",
    "paymentStatus": "PENDING",
    "createdAt": "2024-01-01T12:00:00Z",
    "updatedAt": "2024-01-01T12:00:00Z"
  }
]
```

---

### Get Order by Code

Retrieves a single order by its unique order code.

**Endpoint**: `GET /orders/by-code/{order_code}`

**Path Parameters**:
- `order_code` (required, string): The unique order code (e.g., `ORD-20240101-120000-1234`)

**Response**: `200 OK`

**Response Body**: `OrderOut` object

**Status Codes**:
- `200 OK`: Order found and returned
- `404 Not Found`: Order with the specified code does not exist

**Example Request**:
```
GET /orders/by-code/ORD-20240101-120000-1234
```

**Example Response**: Same as Create Order response

---

### External Status Update

Endpoint designed for external systems (e.g., shipment services) to push status updates to an order. Only fields provided in the payload will be updated. The order code must be provided in the path.

**Endpoint**: `POST /orders/by-code/status-update/{order_code}`

**Path Parameters**:
- `order_code` (required, string): The unique order code

**Request Body**:
```json
{
  "orderStatus": "string (optional)",
  "paymentStatus": "string (optional)",
  "shippingStatus": "string (optional)",
  "shippingOrderCode": "string (optional)",
  "shipper": {
    "shipperId": "string (optional)",
    "name": "string (optional)",
    "phone": "string (optional)",
    "vehicleType": "string (optional: motorbike | car | truck)"
  },
  "estimatedDeliveryTime": "datetime ISO string (optional)",
  "deliveredAt": "datetime ISO string (optional)",
  "failedReason": "string (optional)"
}
```

**Request Schema**: `ExternalStatusUpdate`
- All fields are optional, but at least one should be provided
- `orderStatus` (optional, string): Order status (DRAFT | CONFIRMED | CANCELLED | COMPLETED)
- `paymentStatus` (optional, string): Payment status
- `shippingStatus` (optional, string): Shipping status (NOT_CREATED | CREATED | PICKED | DELIVERING | DELIVERED | FAILED | CANCELLED)
- `shippingOrderCode` (optional, string): Shipping order code from external system
- `shipper` (optional, object): Shipper information
- `estimatedDeliveryTime` (optional, datetime): Estimated delivery time (ISO format)
- `deliveredAt` (optional, datetime): Actual delivery time (ISO format)
- `failedReason` (optional, string): Reason for delivery failure

**Response**: `200 OK`

**Response Body**: `OrderOut` object (updated order)

**Status Codes**:
- `200 OK`: Status updated successfully
- `404 Not Found`: Order with the specified code does not exist

**Example Request**:
```json
{
  "shippingStatus": "DELIVERED",
  "deliveredAt": "2024-01-02T14:30:00Z",
  "orderStatus": "COMPLETED"
}
```

**Example Response**: Same as Create Order response (with updated fields)

**Notes**:
- Only non-null fields in the payload will be updated
- This endpoint is designed for external system integration
- The order code must match an existing order

---

### Update Order

Updates an order's status. Currently, only `orderStatus` can be updated. If updating from PENDING to CANCELLED, the external shipment API is called before updating the database.

**Endpoint**: `PATCH /orders/by-code/{order_code}`

**Path Parameters**:
- `order_code` (required, string): The unique order code

**Request Body**:
```json
{
  "orderStatus": "string (required)"
}
```

**Request Schema**: `OrderUpdate`
- `orderStatus` (required, string): New order status (DRAFT | CONFIRMED | CANCELLED | COMPLETED)

**Response**: `200 OK`

**Response Body**: `OrderOut` object (updated order)

**Status Codes**:
- `200 OK`: Order updated successfully
- `404 Not Found`: Order with the specified code does not exist
- `502 Bad Gateway`: Failed to update shipment status (when cancelling from PENDING)

**Example Request**:
```json
{
  "orderStatus": "CANCELLED"
}
```

**Example Response**: Same as Create Order response (with updated status)

**Notes**:
- Currently only `orderStatus` can be updated
- When cancelling an order with status PENDING, the external shipment API is called first
- If the external API call fails, the database is not updated

---

### Cancel Order

Cancels an order by setting its status to CANCELLED (soft delete). The order is not actually deleted from the database.

**Endpoint**: `DELETE /orders/by-code/{order_code}`

**Path Parameters**:
- `order_code` (required, string): The unique order code

**Response**: `200 OK`

**Response Body**: `OrderOut` object (cancelled order)

**Status Codes**:
- `200 OK`: Order cancelled successfully
- `404 Not Found`: Order with the specified code does not exist

**Example Request**:
```
DELETE /orders/by-code/ORD-20240101-120000-1234
```

**Example Response**: Same as Create Order response (with `orderStatus: "CANCELLED"`)

**Notes**:
- This is a soft delete operation
- The order status is set to `CANCELLED`
- The order remains in the database

---

## Products API

### Create Product

Creates a new product in the catalog. The product ID is automatically generated using UUID.

**Endpoint**: `POST /products`

**Request Body**:
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "price": "float (required, >= 0)",
  "currency": "string (optional, default: VND)",
  "stock": "integer (optional, default: 0, >= 0)",
  "status": "string (optional, default: ACTIVE, values: ACTIVE | INACTIVE)"
}
```

**Request Schema**: `ProductCreate`
- `name` (required, string): Product name
- `description` (optional, string): Product description
- `price` (required, float, >= 0): Product price
- `currency` (optional, string, default: "VND"): Currency code
- `stock` (optional, integer, default: 0, >= 0): Available stock quantity
- `status` (optional, string, default: "ACTIVE"): Product status (ACTIVE | INACTIVE)

**Response**: `201 Created`

**Response Body**: `ProductOut` object (see [Data Models](#data-models))

**Status Codes**:
- `201 Created`: Product created successfully
- `400 Bad Request`: Invalid request data

**Example Request**:
```json
{
  "name": "Wireless Mouse",
  "description": "Ergonomic wireless mouse with USB receiver",
  "price": 250000.0,
  "currency": "VND",
  "stock": 100,
  "status": "ACTIVE"
}
```

**Example Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Wireless Mouse",
  "description": "Ergonomic wireless mouse with USB receiver",
  "price": 250000.0,
  "currency": "VND",
  "stock": 100,
  "status": "ACTIVE",
  "createdAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z"
}
```

**Notes**:
- Product ID is auto-generated using UUID
- Only products with status `ACTIVE` can be added to orders

---

### List Products

Retrieves a paginated list of products, ordered by most recently updated first.

**Endpoint**: `GET /products`

**Query Parameters**:
- `skip` (optional, integer, default: 0): Number of records to skip (for pagination)
- `limit` (optional, integer, default: 50): Maximum number of records to return

**Response**: `200 OK`

**Response Body**: Array of `ProductOut` objects

**Status Codes**:
- `200 OK`: Successfully retrieved products

**Example Request**:
```
GET /products?skip=0&limit=20
```

**Example Response**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Wireless Mouse",
    "description": "Ergonomic wireless mouse with USB receiver",
    "price": 250000.0,
    "currency": "VND",
    "stock": 100,
    "status": "ACTIVE",
    "createdAt": "2024-01-01T12:00:00Z",
    "updatedAt": "2024-01-01T12:00:00Z"
  }
]
```

---

### Get Product

Retrieves a single product by its ID.

**Endpoint**: `GET /products/{product_id}`

**Path Parameters**:
- `product_id` (required, string): The unique product ID (UUID)

**Response**: `200 OK`

**Response Body**: `ProductOut` object

**Status Codes**:
- `200 OK`: Product found and returned
- `404 Not Found`: Product with the specified ID does not exist

**Example Request**:
```
GET /products/550e8400-e29b-41d4-a716-446655440000
```

**Example Response**: Same as Create Product response

---

### Update Product

Updates product information. Only provided fields will be updated.

**Endpoint**: `PATCH /products/{product_id}`

**Path Parameters**:
- `product_id` (required, string): The unique product ID

**Request Body**:
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "price": "float (optional, >= 0)",
  "currency": "string (optional)",
  "stock": "integer (optional, >= 0)",
  "status": "string (optional, values: ACTIVE | INACTIVE)"
}
```

**Request Schema**: `ProductUpdate`
- All fields are optional
- `name` (optional, string): Product name
- `description` (optional, string): Product description
- `price` (optional, float, >= 0): Product price
- `currency` (optional, string): Currency code
- `stock` (optional, integer, >= 0): Available stock quantity
- `status` (optional, string): Product status (ACTIVE | INACTIVE)

**Response**: `200 OK`

**Response Body**: `ProductOut` object (updated product)

**Status Codes**:
- `200 OK`: Product updated successfully
- `404 Not Found`: Product with the specified ID does not exist

**Example Request**:
```json
{
  "price": 230000.0,
  "stock": 95
}
```

**Example Response**: Same as Create Product response (with updated fields)

---

### Delete Product

Permanently deletes a product from the database.

**Endpoint**: `DELETE /products/{product_id}`

**Path Parameters**:
- `product_id` (required, string): The unique product ID

**Response**: `204 No Content`

**Response Body**: None

**Status Codes**:
- `204 No Content`: Product deleted successfully
- `404 Not Found`: Product with the specified ID does not exist

**Example Request**:
```
DELETE /products/550e8400-e29b-41d4-a716-446655440000
```

**Notes**:
- This is a hard delete operation
- The product is permanently removed from the database
- Consider checking for existing orders referencing this product before deletion

---

## Data Models

### Customer

```json
{
  "name": "string",
  "phone": "string",
  "email": "string (optional, EmailStr)"
}
```

### OrderItemCreate

```json
{
  "productId": "string",
  "quantity": "integer (> 0)"
}
```

### OrderItemOut

```json
{
  "id": "integer",
  "productId": "string",
  "productName": "string",
  "quantity": "integer",
  "unitPrice": "float",
  "totalPrice": "float"
}
```

### Pricing

```json
{
  "subTotal": "float (>= 0)",
  "shippingFee": "float (>= 0, default: 0)",
  "discount": "float (>= 0, default: 0)",
  "totalAmount": "float (>= 0)",
  "currency": "string (default: VND)"
}
```

### Address

```json
{
  "receiverName": "string (optional)",
  "receiverPhone": "string (optional)",
  "fullAddress": "string (optional)"
}
```

### Shipper

```json
{
  "shipperId": "string (optional)",
  "name": "string (optional)",
  "phone": "string (optional)",
  "vehicleType": "string (optional: motorbike | car | truck)"
}
```

### Shipping

```json
{
  "shippingOrderCode": "string (optional)",
  "status": "string (default: NOT_CREATED, values: NOT_CREATED | CREATED | PICKED | DELIVERING | DELIVERED | FAILED | CANCELLED)",
  "address": "Address (optional)",
  "shipper": "Shipper (optional)",
  "estimatedDeliveryTime": "datetime ISO string (optional)",
  "deliveredAt": "datetime ISO string (optional)",
  "failedReason": "string (optional)"
}
```

### OrderOut

```json
{
  "id": "UUID",
  "orderCode": "string",
  "customer": "Customer",
  "items": ["OrderItemOut"],
  "pricing": "Pricing",
  "shipping": "Shipping",
  "orderStatus": "string (values: DRAFT | CONFIRMED | CANCELLED | COMPLETED)",
  "paymentMethod": "string (optional, values: COD | BANK_TRANSFER | CREDIT_CARD | PAYPAL)",
  "paymentStatus": "string (default: PENDING)",
  "createdAt": "datetime ISO string",
  "updatedAt": "datetime ISO string"
}
```

### ProductOut

```json
{
  "id": "string (UUID)",
  "name": "string",
  "description": "string (optional)",
  "price": "float (>= 0)",
  "currency": "string (default: VND)",
  "stock": "integer (>= 0)",
  "status": "string (values: ACTIVE | INACTIVE)",
  "createdAt": "datetime ISO string",
  "updatedAt": "datetime ISO string"
}
```

### ExternalStatusUpdate

```json
{
  "orderStatus": "string (optional)",
  "paymentStatus": "string (optional)",
  "shippingStatus": "string (optional)",
  "shippingOrderCode": "string (optional)",
  "shipper": "Shipper (optional)",
  "estimatedDeliveryTime": "datetime ISO string (optional)",
  "deliveredAt": "datetime ISO string (optional)",
  "failedReason": "string (optional)"
}
```

---

## Error Responses

The API uses standard HTTP status codes and returns error details in the response body.

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded, no content to return
- `400 Bad Request`: Invalid request data or validation error
- `404 Not Found`: Resource not found
- `502 Bad Gateway`: External service (shipment API) error

### Error Examples

#### 400 Bad Request

```json
{
  "detail": "Product with ID abc123 not found."
}
```

```json
{
  "detail": "Product abc123 is not active."
}
```

#### 404 Not Found

```json
{
  "detail": "Order not found."
}
```

```json
{
  "detail": "Product not found."
}
```

#### 502 Bad Gateway

```json
{
  "detail": "Failed to create shipment. Order was not created. Please try again."
}
```

```json
{
  "detail": "Failed to cancel shipment. Order status was not updated. Please try again."
}
```

### Validation Rules

#### Order Creation
- `customer.name`: Required, non-empty string
- `customer.phone`: Required, non-empty string
- `customer.email`: Optional, must be valid email format if provided
- `items`: Required, non-empty array
- `items[].productId`: Required, must exist in database and have status ACTIVE
- `items[].quantity`: Required, must be integer > 0

#### Product Creation/Update
- `name`: Required for creation, optional for update
- `price`: Required for creation, optional for update, must be >= 0
- `stock`: Optional, must be >= 0
- `status`: Optional, must be "ACTIVE" or "INACTIVE"
- `currency`: Optional, defaults to "VND"

#### Order Status Values
- `orderStatus`: DRAFT | CONFIRMED | CANCELLED | COMPLETED
- `paymentStatus`: PENDING | SENDER_PAY | RECEIVER_PAY | PREPAID | COD
- `shippingStatus`: NOT_CREATED | CREATED | PICKED | DELIVERING | DELIVERED | FAILED | CANCELLED

#### Payment Method Values
- COD (Cash on Delivery)
- BANK_TRANSFER
- CREDIT_CARD
- PAYPAL

---

## Additional Notes

### Order Code Format
Order codes are automatically generated in the format: `ORD-YYYYMMDD-HHMMSS-XXXX`
- `ORD`: Fixed prefix
- `YYYYMMDD`: Date in UTC
- `HHMMSS`: Time in UTC
- `XXXX`: Random 4-digit suffix

### External Integration
- Orders are automatically sent to an external shipment API upon creation
- If the shipment API call fails, the order is not saved to the database
- Status updates from external systems can be pushed via the `/orders/by-code/status-update/{order_code}` endpoint
- When cancelling a PENDING order, the external shipment API is called before updating the database

### Database
- PostgreSQL database is used
- Tables are auto-created on application startup (use migrations in production)
- Order items are cascade deleted when an order is deleted
- Product relationships are preserved for audit trail (unit price is stored at order time)

### CORS
The API supports CORS (Cross-Origin Resource Sharing) with configurable origins, methods, and headers. Default configuration allows all origins (`*`) for development.

---

## Version Information

- **API Version**: 0.1.0
- **Framework**: FastAPI
- **Python Version**: 3.10+

---

*Last Updated: 2024*

