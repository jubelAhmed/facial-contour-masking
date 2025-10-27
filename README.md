# Facial Contour Masking API

A modern, enterprise-grade FastAPI application for processing facial images and generating SVG contour masks for specific facial regions.

## 🚀 Features

### Core Functionality
- **Facial Image Processing**: Accepts facial images with landmarks and segmentation maps
- **SVG Generation**: Returns SVG contour masks for specific facial regions
- **Face Alignment**: Handles autorotation and cropping of faces
- **Background Job Processing**: Asynchronous image processing with job status tracking
- **Real-time Status Updates**: Poll job status and retrieve results when ready

### Enterprise Features
- **🔐 JWT Authentication**: Secure user authentication with access/refresh tokens
- **🛡️ Security Middleware**: CORS, security headers, and request logging
- **⚡ Rate Limiting**: Redis-backed rate limiting with `slowapi`
- **📊 Monitoring**: Prometheus metrics and Grafana dashboards
- **🗄️ Database Management**: SQLAlchemy ORM with Alembic migrations
- **💾 Perceptual Caching**: Smart caching using image similarity hashing
- **🎨 Rich Logging**: Beautiful console output with structured logging

## 🏗️ Architecture

### System Overview
```
┌─────────────┐     ┌───────────────┐     ┌───────────────┐
│ HTTP Client │────▶│ FastAPI       │────▶│ Background    │
│             │◀────│ API Endpoint  │     │ Job Worker    │
└─────────────┘     └───────────────┘     └───────┬───────┘
                           │                      │
                           ▼                      ▼
                    ┌───────────────┐     ┌───────────────┐
                    │ Database      │◀────│ Image         │
                    │ (Job Queue)   │     │ Processor     │
                    └───────────────┘     └───────────────┘
                           ▲                      │
                           │                      ▼
                    ┌───────────────┐     ┌───────────────┐
                    │ Perceptual    │◀────│ SVG Generator │
                    │ Hash Cache    │     │ & Output      │
                    └───────────────┘     └───────────────┘
```

### Design Patterns

#### **Clean Architecture**
- **Routers**: HTTP layer (controllers)
- **Services**: Business logic layer
- **Repositories**: Data access layer (DAO pattern)
- **Models**: Data structures
- **Shared**: Infrastructure layer

#### **SOLID Principles**
- **Single Responsibility**: Each class has one purpose
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Derived classes are substitutable
- **Interface Segregation**: Small, focused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

#### **Enterprise Patterns**
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic encapsulation
- **Dependency Injection**: Loose coupling
- **Factory Pattern**: Object creation
- **Strategy Pattern**: Algorithm selection

## 📁 Project Structure

```
opnecv_image_processing/
├── .venv/                    # uv virtual environment
├── src/                      # Source code
│   ├── auth/                 # Authentication module
│   │   ├── models.py         # User & token models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── service.py        # Business logic
│   │   ├── repository.py     # Data access layer
│   │   ├── constants.py      # Enums & constants
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── utils.py          # JWT & password utilities
│   ├── facial/               # Facial processing module
│   │   ├── models.py         # Processing models
│   │   ├── schemas.py        # Request/response schemas
│   │   ├── service.py        # Processing logic
│   │   ├── repository.py     # Data access layer
│   │   ├── background_worker.py # Background job processing
│   │   ├── constants.py      # Enums & constants
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── generators/       # Output generators (SVG, PNG, JSON)
│   │   └── facial_processing/ # Core processing
│   ├── shared/               # Shared infrastructure
│   │   ├── config.py         # Configuration management
│   │   ├── database.py       # Database connection
│   │   ├── models.py         # Base models
│   │   ├── exceptions.py     # Global exceptions
│   │   └── utils.py          # Common utilities
│   ├── routers/              # HTTP layer
│   │   ├── auth.py           # Auth endpoints
│   │   └── facial.py         # Processing endpoints
│   ├── internal/             # Internal operations
│   │   └── admin.py          # Admin endpoints
│   ├── middleware/           # Custom middleware
│   │   ├── rate_limiting.py  # Rate limiting with slowapi
│   │   └── security.py       # Security headers
│   ├── monitoring/           # Monitoring setup
│   │   └── prometheus.py     # Prometheus metrics
│   ├── dependencies.py       # Centralized FastAPI dependencies
│   └── main.py              # Application entry point
├── pyproject.toml           # Modern Python project configuration
├── alembic/                 # Database migrations
├── docker/                  # Docker configurations
├── .env.sample              # Environment configuration template
└── templates/               # Static files & dashboards
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd opnecv_image_processing
   ```

2. **Set up virtual environment with uv**
   ```bash
   # Install uv if not already installed
   pip install uv
   
   # Create virtual environment
   uv venv
   
   # Activate virtual environment
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Set up environment configuration**
   ```bash
   # Copy environment template
   cp .env.sample .env
   
   # Edit configuration (optional for development)
   nano .env
   ```

4. **Install dependencies**
   ```bash
   # Install in development mode
   uv pip install -e ".[dev]"
   ```

5. **Run the application**
   ```bash
   # Development mode (uses SQLite by default)
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or with fastapi CLI
   fastapi run src.main:app --reload
   ```

6. **Access the application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Prometheus: http://localhost:9090

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Start all services
docker-compose up --build

# Run in background
docker-compose up -d
```

### Services
- **API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔧 Configuration

### Environment Variables

Copy `.env.sample` to `.env` and configure your settings:

#### Application Settings
- `APP_DEBUG`: Enable debug mode (default: false)
- `APP_APP_NAME`: Application name (default: "Facial Contour Masking API")
- `APP_VERSION`: Application version (default: "1.0.0")

#### Database Settings
- `DB_USE_DATABASE`: Enable/disable database (default: true)
- `DB_HOST`: Database host (default: postgres)
- `DB_PORT`: Database port (default: 5432)
- `DB_USERNAME`: Database username (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres)
- `DB_DATABASE`: Database name (default: facial_api)

#### Authentication Settings
- `AUTH_SECRET_KEY`: JWT secret key (change in production!)
- `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration (default: 60)
- `AUTH_REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration (default: 30)
- `AUTH_ALGORITHM`: JWT algorithm (default: HS256)

#### Rate Limiting Settings
- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: true)
- `RATE_LIMIT_REQUESTS_PER_HOUR`: Requests per hour (default: 100)
- `RATE_LIMIT_WINDOW_SECONDS`: Rate limit window (default: 3600)
- `RATE_LIMIT_BURST_LIMIT`: Burst limit (default: 10)
- `RATE_LIMIT_REDIS_URL`: Redis URL for rate limiting (optional)

#### Monitoring Settings
- `PROMETHEUS_ENABLED`: Enable Prometheus metrics (default: true)
- `PROMETHEUS_PORT`: Prometheus port (default: 9090)

#### Security Settings
- `CORS_ALLOW_ORIGINS`: CORS allowed origins (default: *)
- `TRUSTED_HOSTS`: Trusted hosts (default: *)

## 📚 API Documentation

### Authentication Endpoints

#### POST /auth/register
Register a new user
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secure_password123"
}
```

#### POST /auth/login
Login and get tokens
```json
{
  "username": "johndoe",
  "password": "secure_password123"
}
```

#### POST /auth/refresh
Refresh access token
```json
{
  "refresh_token": "your_refresh_token"
}
```

### Processing Endpoints

#### POST /api/v1/process
Submit facial image for background processing
```json
{
  "image_data": "base64_encoded_image",
  "landmarks": [{"x": 0, "y": 0}, ...],
  "output_format": "svg",
  "style": "default"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Processing job created successfully"
}
```

#### GET /api/v1/status/{job_id}
Check background job status
```json
{
  "job_id": "uuid",
  "status": "completed",
  "result": {
    "contours": [...],
    "style": "default",
    "regions": [...],
    "output_format": "svg",
    "processed_at": "2024-01-01T12:00:00Z"
  },
  "error": null,
  "created_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:00:05Z"
}
```

**Job Status Values:**
- `pending`: Job queued for processing
- `processing`: Currently being processed
- `completed`: Successfully finished
- `failed`: Processing failed

### Background Job Processing

The API uses FastAPI's BackgroundTasks for asynchronous image processing:

1. **Submit Job**: POST `/api/v1/process` returns immediately with job ID
2. **Background Processing**: Image processing happens asynchronously
3. **Status Polling**: GET `/api/v1/status/{job_id}` to check progress
4. **Result Retrieval**: Download processed results when status is "completed"

**Benefits:**
- Non-blocking API responses
- Scalable concurrent processing
- Smart caching prevents duplicate work
- Real-time status updates

### Admin Endpoints

#### GET /admin/users
List all users (superuser only)
```json
[
  {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "is_active": true,
    "is_superuser": false
  }
]
```

## 🗄️ Database Management

### Using Alembic Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Database Models
- **Users**: User authentication and profiles
- **RefreshTokens**: JWT refresh token management
- **ProcessingJobs**: Background job status and results
- **PerceptualHash**: Smart caching for processed images
- **ProcessingMetrics**: Performance metrics

## 🛠️ Development

### Adding Dependencies
```bash
# Install package
uv pip install package-name

# Add to pyproject.toml dependencies section
# Then reinstall to update
uv pip install -e ".[dev]"
```

### Code Quality
```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format and lint code (Ruff handles both)
ruff check src/ --fix
ruff format src/

# Type checking
mypy src/
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_auth.py

# Run with verbose output
uv run pytest -v
```

### Test Structure
```
tests/
├── conftest.py              # Test configuration
├── test_main.py             # Main app tests
├── test_auth.py             # Authentication tests
├── test_facial.py           # Facial processing tests
├── test_facial_generators.py # Generator tests
└── test_facial_service.py   # Service tests
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Password Hashing**: Bcrypt password hashing with strength validation
- **Rate Limiting**: Redis-backed rate limiting with slowapi
- **CORS Protection**: Configurable CORS policies
- **Security Headers**: XSS, CSRF, and content type protection
- **Request Size Limiting**: Protection against large request attacks
- **Input Validation**: Pydantic V2 schema validation
- **Dependency Injection**: Secure dependency management

## 📊 Monitoring & Observability

### Prometheus Metrics
- API request counts and latency
- Image processing time
- Job status distribution
- Authentication events
- Rate limiting violations

### Grafana Dashboards
- Real-time API performance
- Error rates and response times
- User activity and authentication
- System resource usage

## 🚀 Production Deployment

### Environment Setup
1. Copy `.env.sample` to `.env` and configure production values
2. Set `ENV=production` in environment variables
3. Use PostgreSQL for database (`DB_USE_DATABASE=true`)
4. Configure Redis for rate limiting (`RATE_LIMIT_REDIS_URL`)
5. Set secure JWT secret key (`AUTH_SECRET_KEY`)
6. Configure CORS origins (`CORS_ALLOW_ORIGINS`)
7. Set up proper logging and monitoring

### Performance Optimization
- **Database**: PostgreSQL with connection pooling
- **Background Jobs**: Asynchronous image processing with FastAPI BackgroundTasks
- **Caching**: Redis for rate limiting and perceptual hash caching
- **Async Processing**: Non-blocking I/O operations
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Rate Limiting**: Distributed rate limiting with Redis
- **Security**: Request size limiting and security headers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the monitoring dashboards

---

