import uuid
from typing import TYPE_CHECKING, Any, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.context import get_request_context
from app.core.logging import log_user
from app.repositories.exceptions import NotFoundError
from app.user.auth.exceptions import SessionExpiredError
from app.user.auth.service import AuthService
from app.user.dependencies import get_auth_service
from app.user.models import User

if TYPE_CHECKING:
    from app.context import RequestContext


class AuthenticatedUser:
    @classmethod
    async def http_auth(
        cls,
        http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
    ) -> HTTPAuthorizationCredentials:
        return http_auth

    @classmethod
    async def current_user_id(
        cls,
        request: Request,
        http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> uuid.UUID:
        user: User = await cls.load_user_context(request, http_auth, auth_service)
        return user.id

    @classmethod
    async def current_user_email(
        cls,
        request: Request,
        http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> str:
        user: User = await cls.load_user_context(request, http_auth, auth_service)
        return user.email

    @classmethod
    async def load_user_context(
        cls,
        request: Request,
        http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> User:
        if not getattr(request.state, "user", None):
            try:
                user = await auth_service.validate_session(http_auth.credentials)
            except (SessionExpiredError, NotFoundError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=exc.detail,
                ) from exc
            cast("Any", request.state).user = user
            req_ctx: RequestContext = get_request_context()
            req_ctx.user_id = str(user.id)
            req_ctx.email = user.email
            log_user(user.id, user.email)
        return cast("Any", request.state).user
