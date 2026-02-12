"""Sensitive data sanitization for logging."""

from typing import Any

# Keys that should be redacted (case-insensitive partial match)
SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "token",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "credential",
        "credit_card",
        "creditcard",
        "card_number",
        "cvv",
        "ssn",
        "social_security",
        "private_key",
        "privatekey",
        "access_token",
        "refresh_token",
        "bearer",
        "cookie",
        "session_id",
        "sessionid",
    }
)

REDACTED = "[REDACTED]"


def _is_sensitive_key(key: str) -> bool:
    """Check if a key should be redacted."""
    key_lower = key.lower()
    return any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)


def sanitize_value(value: Any) -> Any:
    """Recursively sanitize a value, redacting sensitive data."""
    if isinstance(value, dict):
        return sanitize_dict(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize a dictionary, redacting sensitive fields."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if _is_sensitive_key(key):
            result[key] = REDACTED
        else:
            result[key] = sanitize_value(value)
    return result
