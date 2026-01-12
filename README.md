# Order Services

A RESTful API service for managing orders and products, built with FastAPI and PostgreSQL.

## Project Overview

Order Services is a microservice that provides comprehensive order management functionality, including order creation, status tracking, product management, and integration with external shipping services. The service follows a clean architecture pattern with clear separation between routers, services, and data access layers.

### Key Features

- **Order Management**: Create, update, retrieve, and cancel orders with full lifecycle tracking
- **Product Management**: CRUD operations for product catalog
- **Status Tracking**: Track order status, payment status, and shipping status
- **External Integration**: Integration with external shipping service APIs
- **Data Validation**: Comprehensive input validation using Pydantic schemas
- **Documentation**: Auto-generated API documentation via FastAPI/OpenAPI

## Python Version and Dependencies

### Python Version
- **Python 3.11** (specified in `environment.yml`)

### Core Dependencies

The project uses the following key dependencies (see `environment.yml` for complete list):

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **psycopg2-binary**: PostgreSQL database adapter
- **Pydantic**: Data validation using Python type annotations
- **pydantic-settings**: Settings management using Pydantic models
- **python-dotenv**: Environment variable management

## Project Structure

```
order_services/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application settings and configuration
│   ├── database.py          # Database connection and session management
│   ├── models.py            # SQLAlchemy ORM models (Order, Product, OrderItem)
│   ├── schemas.py           # Pydantic schemas for request/response validation
│   ├── crud.py              # Database CRUD operations
│   ├── services.py          # Business logic and external service integration
│   ├── constants.py         # Application constants
│   └── routers/
│       ├── orders.py        # Order-related API endpoints
│       └── products.py     # Product-related API endpoints
├── logs/                    # Application logs directory
├── validate_documentation.py  # Script to validate code-documentation consistency
├── insert_products.py       # Utility script to insert sample products
├── environment.yml          # Conda environment specification
├── .env                     # Environment variables (not in repo)
├── .gitignore
└── README.md
```

## Key Modules and Responsibilities

### `app/main.py`
- FastAPI application initialization
- CORS middleware configuration
- Router registration
- Database table creation on startup

### `app/config.py`
- Application settings management using Pydantic Settings
- Environment variable loading from `.env` file
- Database connection URL construction
- CORS configuration
- Validation of required configuration parameters

### `app/database.py`
- SQLAlchemy engine creation
- Database session factory
- Session dependency injection for FastAPI routes

### `app/models.py`
- **Order**: Main order entity with customer info, pricing, shipping details, and status tracking
- **Product**: Product catalog with pricing, stock, and status
- **OrderItem**: Junction table linking orders to products with quantity and price snapshots

### `app/schemas.py`
- Pydantic models for request/response validation
- Request schemas: `OrderCreate`, `ProductCreate`, `OrderUpdate`, `ProductUpdate`, `ExternalStatusUpdate`
- Response schemas: `OrderOut`, `ProductOut`, `OrderItemOut`
- Nested models: `Customer`, `Pricing`, `Shipping`, `Address`, `Shipper`

### `app/routers/orders.py`
- `POST /orders`: Create new order
- `GET /orders`: List orders with pagination
- `GET /orders/{order_id}`: Get order by ID
- `GET /orders/by-code/{order_code}`: Get order by order code
- `PATCH /orders/by-code/{order_code}`: Update order status
- `DELETE /orders/by-code/{order_code}`: Cancel order
- `POST /orders/by-code/{order_code}/status-update`: External status update endpoint

### `app/routers/products.py`
- `POST /products`: Create new product
- `GET /products`: List products with pagination
- `GET /products/{product_id}`: Get product by ID
- `PATCH /products/{product_id}`: Update product
- `DELETE /products/{product_id}`: Delete product

### `app/crud.py`
- Database CRUD operations for orders and products
- Order code generation
- Product ID generation
- Query optimization with eager loading

### `app/services.py`
- External shipping service integration
- Address parsing and validation
- HTTP client for external API calls

### Utility Scripts

- **`validate_documentation.py`**: Validates consistency between source code and Excel documentation
- **`insert_products.py`**: Inserts sample products into the database via API

## Setup and Run Instructions

### Prerequisites

- Python 3.11
- PostgreSQL database (local or remote)
- Conda (recommended) or pip for dependency management

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   cd order_services
   ```

2. **Create and activate conda environment**:
   ```bash
   conda env create -f environment.yml
   conda activate order-service
   ```

   Alternatively, using pip:
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic pydantic-settings typing_extensions
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root (see Configuration section below).

4. **Run database migrations** (if using Alembic):
   ```bash
   alembic upgrade head
   ```
   
   Note: The application creates tables automatically on startup if they don't exist (see `app/main.py`). For production, use proper migration tools.

5. **Start the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or using Python directly:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

6. **Access the API**:
   - API Base URL: `http://localhost:8000`
   - Interactive API Docs (Swagger UI): `http://localhost:8000/docs`
   - Alternative API Docs (ReDoc): `http://localhost:8000/redoc`

### Insert Sample Data

To insert sample products for testing:

```bash
python insert_products.py
```

Or specify a custom API URL:
```bash
python insert_products.py http://localhost:8000
```

## Configuration

The application uses environment variables loaded from a `.env` file. Create a `.env` file in the project root with the following variables:

### Database Configuration

**Option 1: Using DATABASE_URL (Recommended)**
```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/database?sslmode=require
```

**Option 2: Using Individual Parameters**
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=order_service_db
```

### Application Settings

```env
# Application name
APP_NAME=order-service

# Application environment (development, staging, production)
APP_ENV=development

# Application port
APP_PORT=8000

# CORS settings (comma-separated or "*" for all)
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*
```

### Environment Variable Notes

- All variables are optional with sensible defaults
- `DATABASE_URL` takes precedence over individual DB parameters if both are set
- If `DATABASE_URL` is not set, all individual DB parameters (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) are required
- CORS origins can be specified as:
  - `*` for all origins (development only)
  - Comma-separated list: `http://localhost:3000,https://example.com`
  - JSON array format: `["http://localhost:3000","https://example.com"]`

### Example `.env` File

```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/orderdb

# Application
APP_NAME=order-service
APP_ENV=development
APP_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_ALLOW_CREDENTIALS=true
```

## API Documentation

Once the application is running, comprehensive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs` - Interactive API explorer
- **ReDoc**: `http://localhost:8000/redoc` - Alternative documentation format

The documentation includes:
- All available endpoints
- Request/response schemas
- Example payloads
- Try-it-out functionality

## Development

### Code Style

The project follows PEP 8 style guidelines and uses type hints throughout. See `.cursorrules` for detailed coding standards.

### Testing

#### Unit Tests

The project includes comprehensive unit tests using pytest. To run the tests:

```bash
# Install pytest if not already installed
pip install pytest pytest-mock

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_services.py
pytest tests/test_crud.py

# Run specific test class or function
pytest tests/test_services.py::TestParseAddress
pytest tests/test_crud.py::TestCreateOrder::test_create_order_success

# Run with coverage report (if pytest-cov is installed)
pytest --cov=app --cov-report=html
```

#### Test Structure

- `tests/conftest.py`: Shared fixtures and test configuration
- `tests/test_services.py`: Tests for external service integration (`app.services`)
- `tests/test_crud.py`: Tests for database CRUD operations (`app.crud`)

#### Test Coverage

The tests cover:
- **Normal (happy path) scenarios**: Successful operations with valid inputs
- **Exception handling**: Error cases and edge conditions
- **Boundary and edge cases**: Empty inputs, None values, boundary conditions
- **External dependencies**: Mocked external API calls and database operations

#### Documentation Validation

Run the documentation validation script:
```bash
python validate_documentation.py
```

### Logging

Application logs are stored in the `logs/` directory (configured in `.gitignore`).

## License

[Specify your license here]

