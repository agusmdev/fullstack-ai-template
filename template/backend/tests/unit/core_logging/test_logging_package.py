"""Direct tests for the app.core.logging package facade.

app/core/logging/__init__.py is a pure re-export module; these tests verify the
public surface (the documented __all__ and that each name resolves to the real
object from its submodule) so a broken import or accidental removal is caught.
"""

import app.core.logging as logging_pkg
from app.core.logging import (
    WideEventContext,
    clear_wide_event_context,
    get_logger,
    get_wide_event_context,
    log_action,
    set_wide_event_context,
)
from app.core.logging import config as _config_mod
from app.core.logging import context as _context_mod
from app.core.logging import helpers as _helpers_mod


class TestPackageSurface:
    def test_all_exports_resolve(self):
        for name in logging_pkg.__all__:
            assert hasattr(logging_pkg, name), (
                f"__all__ lists {name!r} but it is not importable"
            )

    def test_all_exports_are_re_exported_objects(self):
        expected_sources = {
            "configure_logging": _config_mod,
            "get_logger": _config_mod,
            "WideEventContext": _context_mod,
            "get_wide_event_context": _context_mod,
            "set_wide_event_context": _context_mod,
            "clear_wide_event_context": _context_mod,
            "log_action": _helpers_mod,
            "log_custom": _helpers_mod,
            "log_entity": _helpers_mod,
            "log_entities": _helpers_mod,
            "log_user": _helpers_mod,
        }
        for name, source in expected_sources.items():
            package_obj = getattr(logging_pkg, name)
            assert package_obj is getattr(source, name), (
                f"{name} should be re-exported from {source.__name__}"
            )

    def test_all_is_complete(self):
        """__all__ must list every documented public symbol."""
        assert set(logging_pkg.__all__) == {
            "configure_logging",
            "get_logger",
            "WideEventContext",
            "get_wide_event_context",
            "set_wide_event_context",
            "clear_wide_event_context",
            "log_action",
            "log_custom",
            "log_entity",
            "log_entities",
            "log_user",
        }


class TestPackageUsableEndToEnd:
    """The facade functions work when imported through the package path."""

    def test_set_get_clear_context_roundtrip(self):
        ctx = WideEventContext(request_id="req-pkg-1")
        set_wide_event_context(ctx)
        try:
            assert get_wide_event_context() is ctx
            log_action("pkg-create")
            assert ctx.action == "pkg-create"
        finally:
            clear_wide_event_context()
        assert get_wide_event_context() is None

    def test_get_logger_returns_loguru_logger(self):
        from loguru import logger as loguru_logger

        logger = get_logger()
        # get_logger() returns the shared loguru logger used across the app.
        assert logger is loguru_logger
        for method in ("info", "warning", "error", "debug", "bind"):
            assert hasattr(logger, method)
