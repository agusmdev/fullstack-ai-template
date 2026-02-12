"""Tests for sensitive data sanitization."""

import pytest

from app.core.logging.sanitizer import (
    REDACTED,
    SENSITIVE_KEYS,
    _is_sensitive_key,
    sanitize_dict,
    sanitize_value,
)


class TestIsSensitiveKey:
    """Tests for _is_sensitive_key function."""

    @pytest.mark.parametrize(
        "key",
        [
            "password",
            "PASSWORD",
            "user_password",
            "passwd",
            "token",
            "access_token",
            "refresh_token",
            "secret",
            "api_key",
            "apikey",
            "API_KEY",
            "authorization",
            "auth",
            "auth_token",
            "credential",
            "credentials",
            "credit_card",
            "creditcard",
            "card_number",
            "cvv",
            "ssn",
            "social_security",
            "private_key",
            "privatekey",
            "bearer",
            "bearer_token",
            "cookie",
            "session_id",
            "sessionid",
        ],
    )
    def test_sensitive_keys_detected(self, key):
        """Test that sensitive keys are correctly identified."""
        assert _is_sensitive_key(key) is True

    @pytest.mark.parametrize(
        "key",
        [
            "name",
            "email",
            "user_id",
            "id",
            "title",
            "description",
            "amount",
            "status",
            "created_at",
            "updated_at",
            "count",
            "data",
        ],
    )
    def test_non_sensitive_keys_not_detected(self, key):
        """Test that non-sensitive keys are not flagged."""
        assert _is_sensitive_key(key) is False

    def test_case_insensitivity(self):
        """Test that key matching is case insensitive."""
        assert _is_sensitive_key("PASSWORD") is True
        assert _is_sensitive_key("Password") is True
        assert _is_sensitive_key("pAsSwOrD") is True

    def test_partial_match(self):
        """Test that partial matches work (key contains sensitive word)."""
        assert _is_sensitive_key("user_password_hash") is True
        assert _is_sensitive_key("my_secret_key") is True
        assert _is_sensitive_key("x_api_key_header") is True


class TestSanitizeValue:
    """Tests for sanitize_value function."""

    def test_primitive_values_unchanged(self):
        """Test that primitive values pass through unchanged."""
        assert sanitize_value("hello") == "hello"
        assert sanitize_value(123) == 123
        assert sanitize_value(3.14) == 3.14
        assert sanitize_value(True) is True
        assert sanitize_value(None) is None

    def test_dict_sanitized(self):
        """Test that dictionaries are sanitized."""
        result = sanitize_value({"password": "secret123", "name": "test"})
        assert result == {"password": REDACTED, "name": "test"}

    def test_list_items_sanitized(self):
        """Test that list items are recursively sanitized."""
        result = sanitize_value([{"password": "secret"}, {"name": "test"}])
        assert result == [{"password": REDACTED}, {"name": "test"}]

    def test_nested_list(self):
        """Test that nested lists are handled."""
        result = sanitize_value([[{"token": "abc"}]])
        assert result == [[{"token": REDACTED}]]


class TestSanitizeDict:
    """Tests for sanitize_dict function."""

    def test_simple_dict(self):
        """Test sanitizing a simple dictionary."""
        data = {"username": "john", "password": "secret123"}
        result = sanitize_dict(data)
        assert result == {"username": "john", "password": REDACTED}

    def test_nested_dict(self):
        """Test sanitizing nested dictionaries."""
        data = {
            "user": {
                "name": "john",
                "settings": {"api_key": "key123", "secret": "shh"},
            }
        }
        result = sanitize_dict(data)
        assert result == {
            "user": {
                "name": "john",
                "settings": {"api_key": REDACTED, "secret": REDACTED},
            }
        }

    def test_nested_dict_sensitive_key_redacts_entire_value(self):
        """Test that sensitive keys at any level redact entire value."""
        data = {
            "user": {
                "name": "john",
                "credentials": {"api_key": "key123", "secret": "shh"},
            }
        }
        result = sanitize_dict(data)
        # The "credentials" key is sensitive, so the entire value is redacted
        assert result == {
            "user": {
                "name": "john",
                "credentials": REDACTED,
            }
        }

    def test_deeply_nested_dict(self):
        """Test sanitizing deeply nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": {"password": "deep_secret", "data": "safe"},
                }
            }
        }
        result = sanitize_dict(data)
        assert result["level1"]["level2"]["level3"]["password"] == REDACTED
        assert result["level1"]["level2"]["level3"]["data"] == "safe"

    def test_dict_with_list_values(self):
        """Test sanitizing dict containing list values."""
        data = {
            "users": [{"access_token": "abc"}, {"refresh_token": "xyz"}],
            "items": ["a", "b", "c"],
        }
        result = sanitize_dict(data)
        assert result == {
            "users": [{"access_token": REDACTED}, {"refresh_token": REDACTED}],
            "items": ["a", "b", "c"],
        }

    def test_dict_with_sensitive_key_containing_list(self):
        """Test that sensitive key containing list redacts entire value."""
        data = {
            "tokens": [{"access_token": "abc"}, {"refresh_token": "xyz"}],
        }
        result = sanitize_dict(data)
        # "tokens" is a sensitive key, so entire value is redacted
        assert result == {
            "tokens": REDACTED,
        }

    def test_empty_dict(self):
        """Test sanitizing an empty dictionary."""
        assert sanitize_dict({}) == {}

    def test_all_sensitive_keys(self):
        """Test that all known sensitive keys are redacted."""
        # Create a dict with all sensitive keys
        data = {key: f"value_{key}" for key in SENSITIVE_KEYS}
        result = sanitize_dict(data)
        # All values should be redacted
        for key in result:
            assert result[key] == REDACTED

    def test_mixed_sensitive_and_safe(self):
        """Test dict with mix of sensitive and non-sensitive keys."""
        data = {
            "user_id": "123",
            "password": "secret",
            "email": "test@example.com",
            "api_key": "key123",
            "status": "active",
        }
        result = sanitize_dict(data)
        assert result == {
            "user_id": "123",
            "password": REDACTED,
            "email": "test@example.com",
            "api_key": REDACTED,
            "status": "active",
        }

    def test_original_dict_unchanged(self):
        """Test that the original dictionary is not modified."""
        original = {"password": "secret", "name": "test"}
        _ = sanitize_dict(original)
        assert original["password"] == "secret"
