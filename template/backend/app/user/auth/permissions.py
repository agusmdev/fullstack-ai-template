import uuid
from typing import TYPE_CHECKING, Protocol, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.context import ensure_request_context
from app.core.logging import log_user
from app.repositories.exceptions import NotFoundError
from app.user.auth.exceptions import SessionExpiredError
from app.user.auth.service import AuthService
from app.user.dependencies import get_auth_service
from app.user.models import User

if TYPE_CHECKING:
    from app.context import RequestContext


class _RequestState(Protocol):
    """Typed contract for request.state fields set by the auth layer."""

    user: User


def _typed_state(request: Request) -> _RequestState:
    return cast("_RequestState", request.state)


async def _get_authenticated_user(
    request: Request,
    http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Validate session, cache user in request.state, and populate logging context.

    Shared core implementation used by all AuthenticatedUser dependency methods
    to eliminate the duplicated (request, http_auth, auth_service) parameter triple.
    """
    if not getattr(request.state, "user", None):
        try:
            user = await auth_service.validate_session(http_auth.credentials)
        except (SessionExpiredError, NotFoundError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=exc.detail,
            ) from exc
        _typed_state(request).user = user
        req_ctx: RequestContext = ensure_request_context()
        req_ctx.user_id = str(user.id)
        req_ctx.email = user.email
        log_user(user.id, user.email)
    return _typed_state(request).user


class AuthenticatedUser:
    @classmethod
    async def http_auth(
        cls,
        http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
    ) -> HTTPAuthorizationCredentials:
        return http_auth

    @classmethod
    async def load_user_context(
        cls,
        user: User = Depends(_get_authenticated_user),
    ) -> User:
        return user

    @classmethod
    async def current_user_id(
        cls,
        user: User = Depends(_get_authenticated_user),
    ) -> uuid.UUID:
        return user.id

    @classmethod
    async def current_user_email(
        cls,
        user: User = Depends(_get_authenticated_user),
    ) -> str:
        return user.email


async def require_current_user_id(
    user: User = Depends(_get_authenticated_user),
) -> uuid.UUID:
    """Standalone dependency for domain modules that need the current user's ID.

    Domain modules should import this from app.user.auth rather than reaching
    into app.user.auth.permissions directly, to avoid coupling to auth internals.
    """
    return user.id
