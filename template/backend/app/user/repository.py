from app.repositories.sql_repository import SQLAlchemyRepository
from app.user.models import User


class UserRepository(SQLAlchemyRepository[User]):
    model = User
