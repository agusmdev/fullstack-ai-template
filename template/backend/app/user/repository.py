from app.repositories.sql_repository import SQLAlchemyRepository

from .models import User


class UserRepository(SQLAlchemyRepository[User]):
    model = User
