"""
Admin router for system administration operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.models import User
from src.dependencies import get_current_superuser
from src.shared.utils import log_request, log_response, logger

router = APIRouter()


@router.post("/")
async def update_admin(
    request: Request, current_user: User = Depends(get_current_superuser)
):
    """Admin getting schwifty - system update operation."""
    log_request(request, {"user_id": current_user.id, "operation": "admin_update"})

    logger.info(f"Admin operation performed by {current_user.username}")

    response = {"message": "Admin getting schwifty", "admin": current_user.username}
    log_response(request, response)
    return response


@router.get("/system/status")
async def get_system_status(
    request: Request, current_user: User = Depends(get_current_superuser)
):
    """Get system status (admin only)."""
    log_request(request, {"user_id": current_user.id, "operation": "system_status"})

    response = {
        "status": "operational",
        "admin": current_user.username,
        "services": {
            "facial_processing": "running",
            "authentication": "running",
            "database": "connected",
        },
    }

    log_response(request, response)
    return response


@router.get("/users/stats")
async def get_user_stats(
    request: Request, current_user: User = Depends(get_current_superuser)
):
    """Get user statistics (admin only)."""
    log_request(request, {"user_id": current_user.id, "operation": "user_stats"})

    # This would typically query the database for real stats
    response = {
        "total_users": 42,
        "active_users": 38,
        "admin_users": 2,
        "last_updated": "2024-01-01T00:00:00Z",
    }

    log_response(request, response)
    return response
