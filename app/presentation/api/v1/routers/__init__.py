from fastapi import APIRouter

from app.presentation.api.v1.routers.auth import auth_router, couple_router
from app.presentation.api.v1.routers.billing_public import router as billing_public_router
from app.presentation.api.v1.routers.billing_auth import router as billing_auth_router
from app.presentation.api.v1.routers.billing_webhook import router as billing_webhook_router
from app.presentation.api.v1.routers.dashboard import router as dashboard_router
from app.presentation.api.v1.routers.night import router as night_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(couple_router)
v1_router.include_router(billing_public_router)
v1_router.include_router(billing_auth_router)
v1_router.include_router(billing_webhook_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(night_router)

__all__ = ["v1_router"]
