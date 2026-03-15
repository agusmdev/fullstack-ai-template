"""Module with the routers related to the auth service"""

import uuid

import loguru
from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings
from app.user.auth.exceptions import OAuthUserPasswordResetError, UnsupportedOAuthProviderError
from app.user.auth.permissions import AuthenticatedUser
from app.user.auth.schemas import (
    EmailVerificationConfirm,
    EmailVerificationConfirmResponse,
    EmailVerificationResponse,
    LogoutResponse,
    OAuthCallback,
    PasswordResetConfirm,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    SessionResponse,
)
from app.user.auth.service import AuthService
from app.user.dependencies import get_auth_service
from app.user.schemas import UserRegister

auth_router = APIRouter()


@auth_router.post(
    "/login",
    response_description="Login a user using username and password",
    status_code=status.HTTP_200_OK,
)
async def login_user(
    email: str = Body(...),
    password: str = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> SessionResponse:
    return await auth_service.authenticate(email=email, password=password)


@auth_router.post(
    "/register",
    response_description="Register a new user",
)
async def register_user(
    user: UserRegister = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> SessionResponse:
    return await auth_service.register(new_user=user)


@auth_router.post(
    "/logout",
    response_description="Logout current session",
    status_code=status.HTTP_200_OK,
)
async def logout_user(
    http_auth: HTTPAuthorizationCredentials = Depends(AuthenticatedUser.http_auth),
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    """Logout the current user by invalidating their session."""
    await auth_service.logout(http_auth.credentials)
    return LogoutResponse()


@auth_router.post(
    "/logout/all",
    response_description="Logout from all devices",
    status_code=status.HTTP_200_OK,
)
async def logout_all_devices(
    user_id: uuid.UUID = Depends(AuthenticatedUser.current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    """Logout from all devices by invalidating all sessions for the user."""
    await auth_service.logout_all(user_id)
    return LogoutResponse(message="Successfully logged out from all devices")


@auth_router.get(
    "/oauth/{provider}/callback",
    response_description="OAuth callback",
)
async def oauth_callback(
    provider: str,
    auth_service: AuthService = Depends(get_auth_service),
    callback: OAuthCallback = Query(...),
) -> RedirectResponse:
    try:
        session = await auth_service.oauth_login(
            provider_name=provider, payload=callback
        )
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/callback?session={session.id}",
            status_code=status.HTTP_302_FOUND,
        )
    except UnsupportedOAuthProviderError:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/error?error=unsupported_provider",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception:
        loguru.logger.exception("OAuth login failed for provider %s", provider)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/error?error=oauth_login_failed",
            status_code=status.HTTP_302_FOUND,
        )


# Password Reset Endpoints


@auth_router.post(
    "/password/reset",
    response_description="Request password reset email",
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(
    request: PasswordResetRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> PasswordResetResponse:
    """
    Request a password reset email.

    Always returns success to prevent email enumeration attacks.
    If the email exists and is not an OAuth-only account, a reset token will be generated.
    """
    try:
        token = await auth_service.initiate_password_reset(request.email)
    except OAuthUserPasswordResetError:
        # Treat OAuth-only accounts the same as missing users to prevent enumeration
        return PasswordResetResponse()
    if token:
        # TODO: Send email with reset link containing the token
        # Example: send_password_reset_email(request.email, token)
        loguru.logger.info("Password reset token generated — implement email delivery")
    return PasswordResetResponse()


@auth_router.post(
    "/password/confirm",
    response_description="Confirm password reset with token",
    status_code=status.HTTP_200_OK,
)
async def confirm_password_reset(
    request: PasswordResetConfirm = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> PasswordResetConfirmResponse:
    """
    Reset password using a valid token.

    The token is received from the password reset email.
    """
    await auth_service.reset_password(request.token, request.new_password)
    return PasswordResetConfirmResponse()


# Email Verification Endpoints


@auth_router.post(
    "/email/verify",
    response_description="Request email verification",
    status_code=status.HTTP_200_OK,
)
async def request_email_verification(
    user_id: uuid.UUID = Depends(AuthenticatedUser.current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> EmailVerificationResponse:
    """
    Request an email verification link.

    Requires authentication. Generates a verification token and sends an email.
    """
    await auth_service.initiate_email_verification(user_id)
    # TODO: Send email with verification link containing the token
    # Example: send_email_verification_email(user.email, token)
    return EmailVerificationResponse()


@auth_router.post(
    "/email/verify/confirm",
    response_description="Confirm email verification",
    status_code=status.HTTP_200_OK,
)
async def confirm_email_verification(
    request: EmailVerificationConfirm = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> EmailVerificationConfirmResponse:
    """
    Verify email using a valid token.

    The token is received from the verification email.
    """
    await auth_service.verify_email(request.token)
    return EmailVerificationConfirmResponse()
