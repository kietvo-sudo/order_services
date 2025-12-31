# Order System - Source Code Summary

## Project Overview

This is a **FastAPI-based Order Management Service** built with Python 3.11, PostgreSQL, and SQLAlchemy. The system provides a RESTful API for managing e-commerce orders with comprehensive tracking of order status, payment status, and shipping information.

**Technology Stack:**
- **Framework**: FastAPI 0.1.0
- **Database**: PostgreSQL (via SQLAlchemy ORM)
- **Language**: Python 3.11
- **Validation**: Pydantic
- **Configuration**: Pydantic Settings with environment variables

---

## Project Structure

```
Order System/
├── app/                    # Main application package
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Application settings & configuration
│   ├── database.py        # Database connection & session management
│   ├── models.py          # SQLAlchemy database models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py            # Database CRUD operations
│   └── routers/
│       └── orders.py       # Order API endpoints
├── config/
│   └── example.env        # Environment variables template
├── scripts/
│   └── generate_api_excel.py  # API documentation generator
├── tools/
│   └── build_excel.py     # Excel workbook builder for project docs
└── environment.yml        # Conda environment dependencies
```

---

## Core Components

### 1. Application Entry Point (`app/main.py`)

- Initializes FastAPI application with Swagger/ReDoc documentation
- Creates database tables on startup (using SQLAlchemy metadata)
- Registers order router at `/orders` prefix

**Key Features:**
- Auto-generated API docs at `/docs` and `/redoc`
- Database table auto-creation (note: production should use migrations)

### 2. Configuration (`app/config.py`)

Manages application settings via environment variables:

- **Database Configuration**: PostgreSQL connection (host, port, user, password, database name)
- **Application Settings**: App name, environment, port
- Supports full `DATABASE_URL` override or individual connection parameters
- Defaults: `localhost:5434`, database `order_db`

### 3. Database Layer (`app/database.py`)

- Creates SQLAlchemy engine with connection pooling
- Provides `get_db()` dependency for FastAPI route injection
- Uses synchronous SQLAlchemy (not async)

### 4. Data Models (`app/models.py`)

#### **Order Model**
Comprehensive order entity with:
- **Identity**: UUID primary key, unique `order_code`
- **Customer Info**: ID, name, phone, email
- **Pricing**: Subtotal, shipping fee, discount, total amount, currency (default: VND)
- **Payment**: Method, status (default: PENDING)
- **Shipping**: Order code, status (default: NOT_CREATED), receiver details, address
- **Shipper**: JSONB field for shipper information (ID, name, phone, vehicle type)
- **Timestamps**: Delivery estimates, actual delivery time, created/updated timestamps
- **Status Tracking**: Order status (default: CONFIRMED), failed reason
- **Relationships**: One-to-many with `OrderItem`

#### **OrderItem Model**
Order line items:
- **Identity**: Auto-increment integer primary key
- **Product Info**: Product ID, product name
- **Pricing**: Quantity, unit price, total price
- **Relationship**: Foreign key to `Order` with cascade delete

### 5. API Schemas (`app/schemas.py`)

Pydantic models for request/response validation:

**Request Schemas:**
- `Customer`: Customer information (ID, name, phone, email)
- `OrderItemCreate`: Order item creation (product ID/name, quantity, prices)
- `Pricing`: Order pricing breakdown (subtotal, shipping, discount, total, currency)
- `Address`: Shipping address (receiver name, phone, full address)
- `Shipper`: Shipper details (ID, name, phone, vehicle type)
- `Shipping`: Complete shipping information
- `OrderCreate`: Full order creation payload
- `OrderUpdate`: Partial order update (all fields optional)
- `ExternalStatusUpdate`: External system status update payload

**Response Schemas:**
- `OrderOut`: Complete order details with nested objects
- `OrderStatusOut`: Lightweight status-only response
- `OrderItemOut`: Order item details

**Status Enums:**
- **Order Status**: `DRAFT`, `CONFIRMED` (default), `CANCELLED`, `COMPLETED`
- **Payment Status**: `PENDING` (default) + custom values
- **Shipping Status**: `NOT_CREATED` (default), `CREATED`, `PICKED`, `DELIVERING`, `DELIVERED`, `FAILED`, `CANCELLED`

### 6. CRUD Operations (`app/crud.py`)

Database operations layer (separated from routers):

- `create_order()`: Creates new order with items
- `get_orders()`: Lists orders with pagination (skip/limit)
- `get_order()`: Retrieves order by UUID
- `get_order_by_code()`: Retrieves order by order code
- `update_order()`: Updates order fields (status, payment, shipping)
- `delete_order()`: Deletes order (cascades to items)

### 7. API Endpoints (`app/routers/orders.py`)

RESTful API with 8 endpoints:

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `POST` | `/orders` | Create new order | `201: OrderOut` |
| `GET` | `/orders` | List orders (paginated) | `200: List[OrderOut]` |
| `GET` | `/orders/{order_id}` | Get order by UUID | `200: OrderOut` |
| `GET` | `/orders/by-code/{order_code}` | Get order by code | `200: OrderOut` |
| `GET` | `/orders/status/{order_code}` | Get order status (lightweight) | `200: OrderStatusOut` |
| `POST` | `/orders/status-update` | External status update | `200: OrderOut` |
| `PATCH` | `/orders/{order_id}` | Update order | `200: OrderOut` |
| `DELETE` | `/orders/{order_id}` | Delete order | `204: No Content` |

**Key Features:**
- Input validation via Pydantic
- Error handling (400, 404, 422)
- Manual serialization functions (`serialize_order`, `serialize_order_status`)
- Support for external systems to push status updates
- Order code uniqueness validation

---

## Database Schema

### Tables

**`orders`** (Main order table)
- Primary Key: `id` (UUID)
- Unique Constraint: `order_code`
- Foreign Keys: None (parent table)
- JSONB Field: `shipper` (flexible shipper data)
- Timestamps: `created_at`, `updated_at` (auto-managed)

**`order_items`** (Order line items)
- Primary Key: `id` (auto-increment integer)
- Foreign Key: `order_id` → `orders.id` (CASCADE DELETE)
- No unique constraints

---

## Configuration & Environment

### Environment Variables (`.env`)

```env
APP_NAME=order-service
APP_ENV=development
APP_PORT=8000

DB_HOST=localhost
DB_PORT=5434
DB_USER=order_user
DB_PASSWORD=order123
DB_NAME=order_db

# Optional: Full database URL override
# DATABASE_URL=postgresql+psycopg2://user:pass@host:port/db
```

### Dependencies (`environment.yml`)

- Python 3.11
- FastAPI
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)
- psycopg2-binary (PostgreSQL driver)
- Pydantic & Pydantic Settings
- python-dotenv
- typing_extensions

---

## Utility Scripts

### 1. `scripts/generate_api_excel.py`

Generates comprehensive Excel API documentation with styled sheets:
- **Endpoints**: All API endpoints with methods, paths, descriptions
- **Request/Response Schemas**: Field definitions
- **Database Tables**: Schema documentation
- **Status Enums**: Valid status values
- **Metadata**: Generation timestamp, service version

**Output**: `docs/api_documents.xlsx`

### 2. `tools/build_excel.py`

Creates Excel workbook with project overview:
- **Library**: Dependencies list
- **Database Structure**: Table/column definitions
- **Mock Data**: Example field values
- **API List**: Detailed API documentation

**Output**: `order_service_overview.xlsx`

---

## Architecture Patterns

### 1. **Layered Architecture**
- **Router Layer**: HTTP request handling (`routers/orders.py`)
- **Service/CRUD Layer**: Business logic (`crud.py`)
- **Model Layer**: Database models (`models.py`)
- **Schema Layer**: API validation (`schemas.py`)

### 2. **Separation of Concerns**
- Business logic separated from HTTP handling
- Database operations isolated in CRUD functions
- Manual serialization (not using SQLAlchemy's automatic conversion)

### 3. **Dependency Injection**
- FastAPI's `Depends()` for database sessions
- Configuration via Pydantic Settings

### 4. **Data Validation**
- Pydantic schemas for all inputs/outputs
- Field-level validation (e.g., `quantity > 0`, `price >= 0`)
- Email validation for customer emails

---

## Key Features

1. **Order Management**: Full CRUD operations for orders
2. **Status Tracking**: Multi-dimensional status (order, payment, shipping)
3. **External Integration**: Endpoint for external systems to push status updates
4. **Flexible Shipping**: JSONB field for shipper data, supports various vehicle types
5. **Pagination**: List endpoint supports skip/limit
6. **Multiple Lookups**: Find orders by UUID or order code
7. **Lightweight Status Endpoint**: Optimized endpoint for status checks
8. **Documentation**: Auto-generated Swagger/ReDoc + Excel generators

---

## Design Decisions

1. **Synchronous SQLAlchemy**: Uses sync engine (not async) for simplicity
2. **Manual Serialization**: Custom serialization functions instead of automatic ORM conversion
3. **Table Auto-Creation**: Creates tables on startup (production should use Alembic migrations)
4. **Cascade Deletes**: Order items automatically deleted when order is deleted
5. **JSONB for Shipper**: Flexible storage for shipper information
6. **Unique Order Codes**: Database-level uniqueness constraint
7. **Default Statuses**: Sensible defaults (CONFIRMED, PENDING, NOT_CREATED)

---

## API Response Format

All endpoints return consistent JSON structures:
- **Success**: HTTP 200/201 with data payload
- **Error**: HTTP 4xx/5xx with `detail` message
- **Validation Errors**: HTTP 422 with Pydantic validation details

---

## Development Notes

- **Code Quality**: Follows PEP8, uses type hints, production-ready patterns
- **Error Handling**: Explicit error handling with HTTP exceptions
- **Input Validation**: All inputs validated via Pydantic
- **Database**: PostgreSQL with connection pooling
- **Documentation**: Comprehensive API docs via FastAPI + Excel generators

---

## Future Considerations

1. **Migrations**: Replace table auto-creation with Alembic migrations
2. **Async Support**: Consider async SQLAlchemy for better concurrency
3. **Authentication**: Add authentication/authorization middleware
4. **Logging**: Implement structured logging
5. **Testing**: Add pytest test suite
6. **Caching**: Consider Redis for frequently accessed orders
7. **Event System**: Add event publishing for order status changes
8. **Search/Filtering**: Add advanced filtering and search capabilities

---

## Summary Statistics

- **Total Files**: ~10 Python files
- **API Endpoints**: 8 endpoints
- **Database Tables**: 2 tables
- **Pydantic Schemas**: 12+ schemas
- **CRUD Functions**: 6 functions
- **Lines of Code**: ~800+ lines (excluding utilities)

---

*Generated from source code analysis*

