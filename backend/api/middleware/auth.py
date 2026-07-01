"""
JWT Bearer Token Middleware — Phase 10 Production Readiness.

When ``AUTH_ENABLED=true`` in settings every request (except the
exempt paths listed in ``_EXEMPT_PATHS``) must carry a valid
``Authorization: Bearer <token>`` header.

The token is verified using ``backend.core.security.decode_access_token``.
On failure the middleware returns a JSON 401 response directly without
forwarding the request to route handlers.

A companion FastAPI router in ``backend.api.routes.auth`` exposes
``POST /auth/token`` so clients can obtain tokens.
"""

from __future__ import annotations

from typing import Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core.settings import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

# Paths that never require authentication
_EXEMPT_PATHS: Set[str] = {
    "/",
    "/health",
    "/healthz",
    "/readyz",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/token",
    "/auth/token/refresh",
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that enforces JWT Bearer authentication.

    Active only when ``settings.auth_enabled`` is ``True``.
    When disabled this middleware is a transparent pass-through.
    """

    async def dispatch(self, request: Request, call_next):
        # Pass-through when auth is globally disabled
        if not settings.auth_enabled:
            return await call_next(request)

        # Exempt certain paths
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        # OPTIONS preflight — always allow
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "missing_token",
                    "detail": "Authorization header missing or not Bearer scheme.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[len("Bearer "):]
        try:
            from backend.core.security import decode_access_token
            payload = decode_access_token(token)
            # Attach decoded payload for downstream handlers
            request.state.jwt_payload = payload
            request.state.user = payload.get("sub", "anonymous")
        except Exception as exc:
            logger.warning(f"JWT auth failed ({request.url.path}): {exc}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_token",
                    "detail": str(exc),
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)


# Made with Bob
