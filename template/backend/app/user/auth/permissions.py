import uuid
from typing import TYPE_CHECKING, Protocol, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.context import ensure_request_context
from app.core.logging import log_user
from app.repositories.exceptions import NotFoundError
from app.user.auth.dependencies import get_auth_service
from app.user.auth.exceptions import SessionExpiredError
from app.user.auth.service import AuthService
from app.user.models import User

if TYPE_CHECKING:
    from app.core.context import RequestContext


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
    async def current_session_id(
        cls,
        http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
    ) -> str:
        """Return the raw session token without validating it.

        Used by logout endpoints that must succeed even for expired sessions.
        Does NOT guarantee the session exists or is valid.
        """
        return http_auth.credentials

    @classmethod
    async def get_current_user(
        cls,
        user: User = Depends(_get_authenticated_user),
    ) -> User:
        return user

    @classmethod
    async def current_user_id(
        cls,
        user: User = Depends(_get_authenticated_user),
    ) -> uuid.UUID:
        """Return the authenticated user's id.

        Convention: use this classmethod form within the user/ and auth/
        modules' own endpoints. Domain/feature modules (e.g. items) should
        use :func:`require_current_user_id` instead. Both resolve to the same
        underlying dependency; the two entry points exist as an intentional
        convention to keep auth-internal guards visually grouped on
        ``AuthenticatedUser``.
        """
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
    """Return the authenticated user's id.

    Convention: this is the canonical guard for domain/feature modules (e.g.
    items) and should be imported from ``app.user.auth``. The user/ and auth/
    modules use ``AuthenticatedUser.current_user_id`` for their own endpoints.
    The two forms share the exact same implementation; the duplication is an
    intentional convention rather than a behavioral difference.
    """
    return user.id
