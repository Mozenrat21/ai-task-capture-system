from fastapi import APIRouter

from app.config import settings
from app.database import check_database_connection

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("")
def health_check():
    """
    Health check endpoint.

    Checks that backend is alive and database connection works.
    """

    db_is_ok = check_database_connection()

    return {
        "status": "ok" if db_is_ok else "degraded",
        "service": settings.app_name,
        "environment": settings.app_env,
        "database": "ok" if db_is_ok else "error",
    }