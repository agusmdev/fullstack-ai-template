"""Tests for serialized types."""

from datetime import UTC, date, datetime, timezone

import pytest
from pydantic import BaseModel

from app.core.serialized_types import (
    UTCDate,
    UTCDatetime,
    serialize_date,
    serialize_datetime,
)


class TestSerializeDatetime:
    """Tests for serialize_datetime function."""

    def test_utc_datetime(self):
        """Test serializing UTC datetime."""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=UTC)
        result = serialize_datetime(dt)
        assert result == "2024-01-15T12:30:45+00:00"

    def test_naive_datetime_gets_utc(self):
        """Test that naive datetime gets UTC timezone."""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        result = serialize_datetime(dt)
        assert result == "2024-01-15T12:30:45+00:00"

    def test_non_utc_timezone_converted(self):
        """Test that non-UTC timezone is converted to UTC."""
        # Create datetime with +5:00 offset
        tz_plus5 = timezone(offset=__import__("datetime").timedelta(hours=5))
        dt = datetime(2024, 1, 15, 17, 30, 45, tzinfo=tz_plus5)
        result = serialize_datetime(dt)
        # 17:30 + 5:00 offset -> 12:30 UTC
        assert result == "2024-01-15T12:30:45+00:00"

    def test_negative_timezone_converted(self):
        """Test conversion from negative timezone."""
        tz_minus5 = timezone(offset=__import__("datetime").timedelta(hours=-5))
        dt = datetime(2024, 1, 15, 7, 30, 45, tzinfo=tz_minus5)
        result = serialize_datetime(dt)
        # 07:30 - 5:00 offset -> 12:30 UTC
        assert result == "2024-01-15T12:30:45+00:00"

    def test_iso_format_output(self):
        """Test that output is valid ISO format."""
        dt = datetime(2024, 6, 20, 8, 15, 30, tzinfo=UTC)
        result = serialize_datetime(dt)
        # Should be parseable back
        parsed = datetime.fromisoformat(result)
        assert parsed.year == 2024
        assert parsed.month == 6
        assert parsed.day == 20


class TestSerializeDate:
    """Tests for serialize_date function."""

    def test_basic_date(self):
        """Test serializing a basic date."""
        d = date(2024, 1, 15)
        result = serialize_date(d)
        assert result == "2024-01-15"

    def test_different_dates(self):
        """Test serializing different dates."""
        assert serialize_date(date(2024, 12, 31)) == "2024-12-31"
        assert serialize_date(date(2000, 1, 1)) == "2000-01-01"
        assert serialize_date(date(2024, 2, 29)) == "2024-02-29"  # Leap year

    def test_iso_format_output(self):
        """Test that output is valid ISO format."""
        d = date(2024, 6, 20)
        result = serialize_date(d)
        # Should be parseable back
        parsed = date.fromisoformat(result)
        assert parsed == d


class TestUTCDatetimeType:
    """Tests for UTCDatetime annotated type."""

    def test_serialization_in_model(self):
        """Test UTCDatetime serialization in a Pydantic model."""

        class MyModel(BaseModel):
            created_at: UTCDatetime

        dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        model = MyModel(created_at=dt)

        # Check JSON serialization
        json_data = model.model_dump_json()
        assert "2024-01-15T12:00:00+00:00" in json_data

    def test_naive_datetime_in_model(self):
        """Test that naive datetime is handled in model."""

        class MyModel(BaseModel):
            timestamp: UTCDatetime

        dt = datetime(2024, 1, 15, 12, 0, 0)  # Naive
        model = MyModel(timestamp=dt)

        json_data = model.model_dump_json()
        assert "2024-01-15T12:00:00+00:00" in json_data


class TestUTCDateType:
    """Tests for UTCDate annotated type."""

    def test_serialization_in_model(self):
        """Test UTCDate serialization in a Pydantic model."""

        class MyModel(BaseModel):
            birth_date: UTCDate

        d = date(1990, 5, 15)
        model = MyModel(birth_date=d)

        # Check JSON serialization
        json_data = model.model_dump_json()
        assert "1990-05-15" in json_data

    def test_dict_serialization(self):
        """Test that dict serialization works normally."""

        class MyModel(BaseModel):
            event_date: UTCDate

        d = date(2024, 12, 25)
        model = MyModel(event_date=d)

        # model_dump without mode='json' should return date object
        data = model.model_dump()
        assert data["event_date"] == d


class TestTypesExported:
    """Tests for module exports."""

    def test_utc_datetime_exported(self):
        """Test UTCDatetime is properly exported."""
        from app.core.serialized_types import UTCDatetime

        assert UTCDatetime is not None

    def test_utc_date_exported(self):
        """Test UTCDate is properly exported."""
        from app.core.serialized_types import UTCDate

        assert UTCDate is not None
