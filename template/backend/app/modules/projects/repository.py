"""Project repository — data access layer."""

from app.modules.projects.models import Project
from app.repositories.sql_repository import SQLAlchemyRepository


class ProjectRepository(SQLAlchemyRepository[Project]):
    """Repository for Project entity."""

    model = Project
