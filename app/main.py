from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.api.routes import vibe as vibe_routes
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy metadata is fully populated for optional local startup.
from app import models as _models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    if settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.include_router(api_router)
# The build contract names the canonical paths under /v1. Keep the existing
# repository /api/v1 prefix as a compatibility mount without changing the
# underlying trigger or serialization behavior.
app.include_router(vibe_routes.router, prefix="/v1")


@app.get("/health", tags=["health"])
def root_health_check() -> dict[str, str]:
    return {"status": "ok"}
