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
   
   **Option 1: Using start script (recommended for production)**:
   ```bash
   ./start.sh
   ```
   This script automatically uses the `PORT` environment variable if set (for cloud platforms like Render).

   **Option 2: Direct uvicorn command**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}
   ```

   **Option 3: Using Python directly**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}
   ```

   **Note**: The `PORT` environment variable is automatically used if set (e.g., on Render, Heroku). Defaults to 8000 if not set.

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

The application uses environment variables loaded from a `.env` file. Create a `.env` file in the project root with the following variables.

**Quick Start**: Copy `env.example` to `.env` and fill in your values:
```bash
cp env.example .env
# Then edit .env with your actual values
```

### All Environment Variables

#### Application Settings
```env
APP_NAME=order-service              # Application name
APP_ENV=development                 # Environment: development, staging, production
APP_PORT=8000                       # Application port (default: 8000)
PORT=8000                           # Used by cloud platforms (Render, Heroku). Overrides APP_PORT if set.
```

#### Database Configuration

**Option 1: Using DATABASE_URL (Recommended for cloud databases)**
```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/database?sslmode=require
```

**Option 2: Using Individual Parameters** (if DATABASE_URL is not set)
```env
DB_HOST=localhost                   # Database hostname
DB_PORT=5432                        # Database port
DB_USER=postgres                    # Database username
DB_PASSWORD=your_password_here     # Database password
DB_NAME=orderdb                     # Database name
```

**Important**: 
- `DATABASE_URL` takes precedence over individual DB parameters if both are set
- If `DATABASE_URL` is not set, **all** individual DB parameters (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) are **required**

#### CORS Settings
```env
CORS_ORIGINS=*                      # All origins (development) or comma-separated list
CORS_ALLOW_CREDENTIALS=false       # Allow credentials (must be false if CORS_ORIGINS=*)
CORS_ALLOW_METHODS=*               # Allowed HTTP methods
CORS_ALLOW_HEADERS=*               # Allowed HTTP headers
```

CORS origins can be specified as:
- `*` for all origins (development only)
- Comma-separated list: `https://your-frontend.com,https://another-domain.com`

### Complete Example `.env` File

```env
# ============================================
# Application Settings
# ============================================
APP_NAME=order-service
APP_ENV=development
APP_PORT=8000
PORT=8000

# ============================================
# Database Configuration
# ============================================
# Option 1: Using DATABASE_URL (Recommended)
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/orderdb

# Option 2: Using Individual Parameters (if DATABASE_URL is not set)
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=your_password_here
# DB_NAME=orderdb

# ============================================
# CORS Settings
# ============================================
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=false
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*
```

### Environment Variable Notes

- All variables are optional with sensible defaults (except database settings)
- `PORT` environment variable (from cloud platforms) automatically overrides `APP_PORT`
- `DATABASE_URL` takes precedence over individual DB parameters if both are set
- If `DATABASE_URL` is not set, all individual DB parameters are required
- See `env.example` file for a complete template

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

