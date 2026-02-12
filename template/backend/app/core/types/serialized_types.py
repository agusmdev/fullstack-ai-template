from datetime import UTC, date, datetime
from typing import Annotated

from pydantic import PlainSerializer


def serialize_datetime(dt: datetime) -> str:
    """Convert datetime to UTC and return ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def serialize_date(d: date) -> str:
    """Convert date to ISO format string."""
    return d.isoformat()


# Custom type for UTC datetime with ISO format serialization
UTCDatetime = Annotated[
    datetime, PlainSerializer(serialize_datetime, return_type=str, when_used="json")
]

# Custom type for date with ISO format serialization
UTCDate = Annotated[
    date, PlainSerializer(serialize_date, return_type=str, when_used="json")
]

__all__ = ["UTCDatetime", "UTCDate"]
