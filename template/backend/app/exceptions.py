"""Base module for HTTP Exceptions"""

from typing import Any

from fastapi import HTTPException


class HTTPExceptionMixin(HTTPException):
    """Base HTTP exception"""

    error_code = "internal_server_error"
    detail = "Internal Server Error"
    status_code = 500

    def __init__(
        self, *, status_code: int | None = None, detail: Any = None, **kwargs: Any
    ) -> None:
        super().__init__(
            status_code=status_code or self.status_code,
            detail=detail or self.detail,
            **kwargs,
        )
