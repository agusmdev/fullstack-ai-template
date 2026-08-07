"""Repository exceptions"""

from app.exceptions import HTTPExceptionMixin


class RepositoryError(HTTPExceptionMixin):
    detail = "Repository error"
    error_code = "repository_error"
    status_code = 500


class NotFoundError(RepositoryError):
    detail = "Item not found"
    error_code = "not_found"
    status_code = 404


class DuplicateError(RepositoryError):
    detail = "Item already exists"
    error_code = "duplicate_item"
    status_code = 400


class ReferencedError(RepositoryError):
    detail = "Item is referenced by other items"
    error_code = "referenced_item"
    status_code = 400


class ForbiddenError(RepositoryError):
    """The user is authenticated and a member of the team, but lacks the role
    required for the requested action (e.g. a ``guest`` attempting a write, or a
    ``member`` attempting an admin-only action).

    Distinct from :class:`NotFoundError` (404), which signals that the user is
    *not a member* of the team — used for cross-team denial so a team's existence
    is never leaked.
    """

    detail = "Insufficient permissions for this action"
    error_code = "forbidden"
    status_code = 403
