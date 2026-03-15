# AuthenticatedUser has moved to app.user.auth.permissions.
# This re-export exists for backwards compatibility.
from app.user.auth.permissions import AuthenticatedUser

__all__ = ["AuthenticatedUser"]
