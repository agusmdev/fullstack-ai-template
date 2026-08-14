"""Dependency factory functions for User module.

Auth DI lives in app/user/auth/dependencies.py so the auth package owns its
full DI surface.
"""

from fastapi import Depends

from app.dependencies import get_repository
from app.user.repository import UserRepository
from app.user.service import UserService


def get_user_service(
    repo: UserRepository = Depends(get_repository(UserRepository)),
) -> UserService:
    return UserService(repo=repo)
