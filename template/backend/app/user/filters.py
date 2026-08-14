from fastapi_filter.contrib.sqlalchemy import Filter

from app.user.models import User


class UserFilter(Filter):
    order_by: list[str] = ["created_at"]
    email: str | None = None
    search: str | None = None

    class Constants(Filter.Constants):
        model = User
        search_model_fields = [
            "email",
            "display_name",
        ]
        search_field_name = "search"
