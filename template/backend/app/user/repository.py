import uuid

from pydantic import BaseModel

from app.repositories.sql_repository import SQLAlchemyRepository

from .models import User


class UserRepository(SQLAlchemyRepository[User]):
    model = User

    async def get(
        self,
        entity_id: uuid.UUID | str,
        raise_error: bool = True,
        filter_field: str = "id",
        response_model: type[BaseModel] | None = None,
    ) -> User | None:
        """Get a user by ID or by another field (e.g., email)."""
        if filter_field == "id" and isinstance(entity_id, str):
            entity_id = uuid.UUID(entity_id)
        return await super().get(
            entity_id,
            raise_error=raise_error,
            filter_field=filter_field,
            response_model=response_model,
        )
