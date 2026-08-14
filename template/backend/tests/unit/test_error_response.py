"""The custom HTTP exception handler surfaces error_code to clients."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import ErrorResponse
from app.main import _http_exception_handler
from app.repositories.exceptions import NotFoundError


def _app_with_handler() -> FastAPI:
    from fastapi import HTTPException

    app = FastAPI()
    app.add_exception_handler(HTTPException, _http_exception_handler)

    @app.get("/not-found")
    async def _raise_not_found() -> None:
        raise NotFoundError(detail="missing")

    @app.get("/vanilla")
    async def _raise_vanilla() -> None:
        raise HTTPException(status_code=418, detail="teapot")

    @app.get("/with-headers")
    async def _raise_with_headers() -> None:
        raise HTTPException(
            status_code=401,
            detail="no",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return app


class TestErrorResponseContract:
    def test_error_response_schema_defaults(self):
        body = ErrorResponse().model_dump(mode="json")
        assert body == {
            "detail": "Internal Server Error",
            "error_code": "internal_server_error",
        }

    def test_mixin_subclass_error_code_reaches_client(self):
        client = TestClient(_app_with_handler())
        resp = client.get("/not-found")
        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"] == "missing"
        assert body["error_code"] == "not_found"

    def test_vanilla_http_exception_gets_default_error_code(self):
        client = TestClient(_app_with_handler())
        resp = client.get("/vanilla")
        assert resp.status_code == 418
        body = resp.json()
        assert body["detail"] == "teapot"
        assert body["error_code"] == "http_error"

    def test_exception_headers_are_forwarded(self):
        client = TestClient(_app_with_handler())
        resp = client.get("/with-headers")
        assert resp.status_code == 401
        assert resp.headers["WWW-Authenticate"] == "Bearer"
        assert resp.json()["error_code"] == "http_error"

    def test_handler_is_registered_in_create_app(self):
        # The handler must be wired for the base HTTPException so all subclasses surface error_code.
        from fastapi import HTTPException

        from app.main import create_app

        app = create_app(add_sentry=False)
        assert HTTPException in app.exception_handlers
