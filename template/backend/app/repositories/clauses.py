from collections.abc import Callable
from typing import Any

from sqlalchemy.dialects.postgresql import Insert as PGInsert

OnConflictClause = Callable[..., PGInsert]


def conflict_do_nothing(insert: PGInsert, **kwargs: Any) -> PGInsert:
    return insert.on_conflict_do_nothing(**kwargs)


def conflict_do_update(insert: PGInsert, **kwargs: Any) -> PGInsert:
    return insert.on_conflict_do_update(**kwargs)


def conflict_passthrough(insert: PGInsert) -> PGInsert:
    """Return the insert statement unchanged — no conflict handling."""
    return insert
