"""Module with the routers related to the user service"""

import uuid

from fastapi import APIRouter, Body, Depends, status

from app.user.auth.permissions import AuthenticatedUser
from app.user.models import User

from app.user.dependencies import get_user_service
from app.user.schemas import UserResponse, UserUpdate
from app.user.service import UserService

user_router = APIRouter(dependencies=[Depends(AuthenticatedUser.current_user_id)])


@user_router.get(
    "/me",
    response_description="Get the logged user profile",
    status_code=status.HTTP_200_OK,
)
async def get_authenticated_user(
    user: User = Depends(AuthenticatedUser.load_user_context),
) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
    )


@user_router.patch(
    "/me",
    response_description="Update user",
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_logged_user(
    user_id: uuid.UUID = Depends(AuthenticatedUser.current_user_id),
    user: UserUpdate = Body(...),
    user_service: UserService = Depends(get_user_service),
) -> None:
    await user_service.update(user_id, user)


@user_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete user",
)
async def delete_user(
    user_id: uuid.UUID = Depends(AuthenticatedUser.current_user_id),
    user_service: UserService = Depends(get_user_service),
) -> None:
    await user_service.delete(user_id)
