"""User authentication package — public boundary.

Domain modules that need auth dependencies should import from this package
rather than from submodules directly, to stay isolated from internal changes.
"""

from app.user.auth.permissions import AuthenticatedUser, require_current_user_id

__all__ = ["AuthenticatedUser", "require_current_user_id"]
