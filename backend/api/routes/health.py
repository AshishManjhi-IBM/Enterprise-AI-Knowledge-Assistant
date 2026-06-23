"""
Health check endpoints.
"""

from fastapi import APIRouter
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        dict: Health status
    """
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "service": "rag-platform"
    }


@router.get("/healthz")
async def healthz():
    """
    Kubernetes-style health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "ok"}


@router.get("/readyz")
async def readyz():
    """
    Kubernetes-style readiness check endpoint.
    
    Returns:
        dict: Readiness status
    """
    return {"status": "ready"}

# Made with Bob
