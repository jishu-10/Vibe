from __future__ import annotations

import secrets

from fastapi import HTTPException, Request

from app.core.config import get_settings
from app.db.session import get_db


def require_vibe_service_authorization(request: Request) -> None:
    """Authorize Vibe routes at the application-service boundary.

    Local test/development execution is process-trusted. Non-local execution
    must configure an explicit service token and present it as a Bearer token;
    an absent or mismatched token fails closed.
    """
    settings = get_settings()
    if settings.environment == "local" and settings.vibe_service_token is None:
        return
    expected = settings.vibe_service_token
    if not expected:
        raise HTTPException(status_code=503, detail={"code": "AUTHORIZATION_REQUIRED", "path": "vibe.authorization", "message": "Vibe service authorization is not configured."})
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "path": "vibe.authorization", "message": "Vibe service authorization failed."})

__all__ = ["get_db", "require_vibe_service_authorization"]
