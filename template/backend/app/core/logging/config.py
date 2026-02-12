"""Logging configuration using loguru."""

import logging
import sys
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    import loguru

from app.core.config import settings


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


def _get_log_level() -> str:
    """Get log level from settings, defaulting to INFO."""
    level = getattr(settings, "LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    return level if level in valid_levels else "INFO"


def _get_log_format() -> str:
    """Get log format from settings."""
    return getattr(settings, "LOG_FORMAT", "console")


def _serialize_record(record: dict[str, Any]) -> str:
    """Custom serializer for JSON output."""
    import json
    from datetime import datetime

    subset = {
        "timestamp": datetime.now().isoformat(),
        "level": record["level"].name.lower(),
        "message": record["message"],
        "logger": record["name"],
    }

    # Add extra bound context
    if record.get("extra"):
        for key, value in record["extra"].items():
            if not key.startswith("_"):
                subset[key] = value

    # Add exception info if present
    if record["exception"]:
        subset["exception"] = {
            "type": record["exception"].type.__name__
            if record["exception"].type
            else None,
            "value": str(record["exception"].value)
            if record["exception"].value
            else None,
        }

    return json.dumps(subset, default=str) + "\n"


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

    if use_json:
        # JSON output for production
        logger.add(
            sys.stdout,
            format="{message}",
            serialize=True,
            level=log_level,
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
        )

    # Bind environment context that will be included in all logs
    env_context = {
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }

    # Add optional deployment context
    if hasattr(settings, "VERSION") and settings.VERSION:
        env_context["version"] = settings.VERSION
    if hasattr(settings, "COMMIT_HASH") and settings.COMMIT_HASH:
        env_context["commit_hash"] = settings.COMMIT_HASH
    if hasattr(settings, "INSTANCE_ID") and settings.INSTANCE_ID:
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
            logging.getLogger(logger_name).setLevel(logging.INFO)
        else:
            logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger() -> "loguru.Logger":
    """Get the configured loguru logger instance."""
    return logger
