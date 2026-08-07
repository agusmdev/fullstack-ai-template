"""Label repository — data access layer."""

from app.modules.labels.models import Label
from app.repositories.sql_repository import SQLAlchemyRepository


class LabelRepository(SQLAlchemyRepository[Label]):
    """Repository for Label entity."""

    model = Label
