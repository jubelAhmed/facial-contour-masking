"""
Main application module that defines FastAPI routes and startup/shutdown events.
Following FastAPI's recommended project structure.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from slowapi.errors import RateLimitExceeded

# Import dependencies
from src.dependencies import get_query_token, get_token_header

# Import internal modules
from src.internal import admin

# Import routers
from src.routers import auth, facial

# Import core modules
from src.core.config import config
from src.core.database import create_db_and_tables
from src.core.utils import log_startup_banner, log_processing_step
from src.middleware.rate_limiting import limiter, rate_limit_exceeded_handler
from src.middleware.security import SecurityHeadersMiddleware, RequestLoggingMiddleware, CORSSecurityMiddleware

# Initialize FastAPI app with global dependencies
app = FastAPI(
    title=config.app_name, 
    description="API for processing facial images and generating contour masks",
    version=config.version,
    debug=config.debug,
    dependencies=[Depends(get_query_token)]  # Global dependency
)

# Add security middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware with security considerations
app.add_middleware(
    CORSSecurityMiddleware,
    allowed_origins=["*"],  # Configure for production
    allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Add rate limiting with slowapi
if config.rate_limit.enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add Prometheus middleware
from src.monitoring.prometheus import PrometheusMiddleware, setup_prometheus
app.add_middleware(PrometheusMiddleware)

# Include API routers
app.include_router(auth.router)
app.include_router(facial.router)

# Include admin router with custom prefix, tags, dependencies, and responses
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)

# Display startup banner
log_startup_banner("Facial Contour Masking API", "1.0.0")

# Setup Prometheus metrics server and database connections
@app.on_event("startup")
async def startup_event():
    # Start Prometheus metrics server if enabled
    if config.prometheus.enabled:
        setup_prometheus(port=config.prometheus.port)
        log_processing_step("Prometheus metrics server started")
    
    # Initialize database if enabled
    if config.db.use_database:
        log_processing_step("Initializing database...")
        await create_db_and_tables()
        log_processing_step("Database initialization completed")
    else:
        log_processing_step("Database usage is disabled")

@app.on_event("shutdown")
async def shutdown_event():
    # Close database connections if database was used
    if config.db.use_database:
        from src.core.database import db_manager
        await db_manager.close()
        log_processing_step("Database connections closed")

@app.get("/")
async def root():
    """Root endpoint with application information."""
    return {
        "message": "Hello Bigger Applications!",
        "service": config.app_name,
        "version": config.version,
        "status": "operational",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration systems."""
    db_status = "connected" if config.db.use_database else "disabled"
    
    return {
        "status": "healthy",
        "service": config.app_name,
        "version": config.version,
        "database": db_status,
        "timestamp": str(datetime.now())
    }