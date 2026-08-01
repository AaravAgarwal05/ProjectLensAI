"""Top-level v1 API router aggregating all endpoint modules."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.api.v1 import (
    analysis,
    auth,
    chat,
    collections,
    documents,
    eval_runs,
    health,
    reports,
    settings,
)

api_router = APIRouter()

# Endpoints behind the JWT — every route in these routers requires a valid token.
_auth_required = [Depends(get_current_user)]

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", dependencies=_auth_required, tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", dependencies=_auth_required, tags=["chat"])
api_router.include_router(analysis.router, prefix="/analysis", dependencies=_auth_required, tags=["analysis"])
api_router.include_router(reports.router, prefix="/reports", dependencies=_auth_required, tags=["reports"])
api_router.include_router(collections.router, prefix="/collections", dependencies=_auth_required, tags=["collections"])
api_router.include_router(settings.router, prefix="/settings", dependencies=_auth_required, tags=["settings"])
api_router.include_router(eval_runs.router, prefix="/eval", dependencies=_auth_required, tags=["eval"])
