from collections.abc import Callable
from typing import Any

from sqlalchemy.dialects.postgresql import Insert as PGInsert

OnConflictClause = Callable[[PGInsert], PGInsert]


def do_nothing_on_conflict(insert: PGInsert, **kwargs: Any) -> PGInsert:
    return insert.on_conflict_do_nothing(**kwargs)


def do_update_on_conflict(insert: PGInsert, **kwargs: Any) -> PGInsert:
    return insert.on_conflict_do_update(**kwargs)


def do_default_on_conflict(insert: PGInsert) -> PGInsert:
    return insert
