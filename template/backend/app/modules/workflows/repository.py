"""WorkflowState repository — data access layer."""

from app.modules.workflows.models import WorkflowState
from app.repositories.sql_repository import SQLAlchemyRepository


class WorkflowStateRepository(SQLAlchemyRepository[WorkflowState]):
    """Repository for WorkflowState entity."""

    model = WorkflowState
