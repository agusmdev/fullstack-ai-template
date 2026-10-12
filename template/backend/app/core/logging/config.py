"""Logging configuration using loguru."""

import logging
import sys

from loguru import logger

from app.core.config import settings
from app.core.logging.sanitizer import sanitize_query_string


class InterceptHandler(logging.Handler):
    """Intercept stdlib logging and route to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class RedactAccessLogQuery(logging.Filter):
    """Redact sensitive query params in uvicorn access lines.

    uvicorn logs ``'%s - "%s %s HTTP/%s" %d'`` with the path and query string
    as the third argument; without this filter a token passed in the query
    string would reach the logs in plain text.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) >= 3 and isinstance(args[2], str):
            path, separator, query = args[2].partition("?")
            if separator:
                record.args = (
                    *args[:2],
                    f"{path}?{sanitize_query_string(query)}",
                    *args[3:],
                )
        return True


def _get_log_level() -> str:
    """Get log level from settings, defaulting to INFO."""
    level = settings.LOG_LEVEL.upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    return level if level in valid_levels else "INFO"


def _get_log_format() -> str:
    """Get log format from settings."""
    return settings.LOG_FORMAT


def configure_logging() -> None:
    """Configure loguru for the application.

    - JSON output for production (ENVIRONMENT != local)
    - Pretty console output for local development
    - Intercepts stdlib logging (SQLAlchemy, httpx, uvicorn, etc.)
    """
    # Remove default handler
    logger.remove()

    log_level = _get_log_level()
    log_format = _get_log_format()

    # Determine if we should use JSON based on environment or explicit format
    use_json = log_format == "json" or (
        log_format != "console" and settings.ENVIRONMENT != "local"
    )

    # Tracebacks never show variable values (diagnose) or frames outside the
    # catch point (backtrace): local variables hold passwords, password hashes
    # and tokens, and a traceback must not print them.
    if use_json:
        # JSON output for production
        logger.add(
            sys.stdout,
            format="{message}",
            serialize=True,
            level=log_level,
            backtrace=False,
            diagnose=False,
        )
    else:
        # Pretty console output for local development
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
            level=log_level,
            backtrace=False,
            diagnose=False,
        )

    # Bind environment context that will be included in all logs
    env_context = {
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }

    # Add optional deployment context
    if settings.VERSION:
        env_context["version"] = settings.VERSION
    if settings.COMMIT_HASH:
        env_context["commit_hash"] = settings.COMMIT_HASH
    if settings.INSTANCE_ID:
        env_context["instance_id"] = settings.INSTANCE_ID

    logger.configure(extra=env_context)

    # Intercept stdlib logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set specific library log levels to reduce noise
    for logger_name in [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "httpx",
        "httpcore",
    ]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
        # Keep uvicorn.access at INFO for request logs, others at WARNING
        if logger_name == "uvicorn.access":
            access_logger = logging.getLogger(logger_name)
            access_logger.setLevel(logging.INFO)
            if not any(
                isinstance(f, RedactAccessLogQuery) for f in access_logger.filters
            ):
                access_logger.addFilter(RedactAccessLogQuery())
        else:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
