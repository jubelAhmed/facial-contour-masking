"""
Main application module that defines FastAPI routes and startup/shutdown events.
Following FastAPI's recommended project structure.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

# Import dependencies
from src.dependencies import get_query_token, get_token_header

# Import internal modules
from src.internal import admin
from src.middleware.rate_limiting import (
    SlowAPIMiddleware,
    limiter,
    rate_limit_exceeded_handler,
)
from src.middleware.security import SecurityHeadersMiddleware

# Import routers
from src.routers import auth, facial

# Import core modules
from src.shared.config import config
from src.shared.database import create_db_and_tables, db_manager
from src.shared.utils import log_processing_step, log_startup_banner

# Import background worker
from src.facial.background_worker import start_background_worker, stop_background_worker


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if config.prometheus.enabled:
        setup_prometheus(port=config.prometheus.port)
        log_processing_step("Prometheus metrics server started")

    if config.db.use_database:
        log_processing_step("Initializing database...")
        await create_db_and_tables()
        log_processing_step("Database initialization completed")
        
        # Start background worker for job processing
        log_processing_step("Starting background job worker...")
        # Note: Background worker would need proper dependency injection
        # await start_background_worker(job_repo, hash_repo, db_manager)
        log_processing_step("Background job worker started")
    else:
        log_processing_step("Database usage is disabled")

    yield

    # Shutdown
    if config.db.use_database:
        # Stop background worker
        log_processing_step("Stopping background job worker...")
        await stop_background_worker()
        log_processing_step("Background job worker stopped")
        
        await db_manager.close()
        log_processing_step("Database connections closed")


# Initialize FastAPI app with global dependencies
app = FastAPI(
    title=config.app_name,
    description="API for processing facial images and generating contour masks",
    version=config.version,
    debug=config.debug,
    dependencies=[Depends(get_query_token)],  # Global dependency
    lifespan=lifespan,  # Modern lifespan handler
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting with slowapi
if config.rate_limit.enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

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


@app.get("/")
async def root():
    """Root endpoint with application information."""
    return {
        "message": "Hello Bigger Applications!",
        "service": config.app_name,
        "version": config.version,
        "status": "operational",
        "docs_url": "/docs",
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
        "timestamp": str(datetime.now()),
    }
