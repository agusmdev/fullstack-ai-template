"""Module for including all the app's routers"""

from fastapi import APIRouter, Depends

from app.core.permissions.auth import AuthenticatedUser
from app.modules.items.routers import items_router
from app.user.auth.routers import auth_router
from app.user.routers import router as user_router


def get_app_router() -> APIRouter:
    router = APIRouter()

    router.include_router(
        auth_router,
        prefix="/auth",
        tags=["auth"],
    )

    router.include_router(
        user_router,
        prefix="/users",
        tags=["users"],
    )

    router.include_router(items_router)

    return router
