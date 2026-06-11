from fastapi import FastAPI

from app.config import settings
from app.routers.dicts import router as dicts_router
from app.routers.health import router as health_router
from app.routers.tasks import router as tasks_router



app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Personal AI-powered task capture system with preview-confirm workflow.",
)

app.include_router(health_router)
app.include_router(dicts_router)
app.include_router(tasks_router)
@app.get("/")
def root():
    """
    Root endpoint.
    """

    return {
        "service": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }