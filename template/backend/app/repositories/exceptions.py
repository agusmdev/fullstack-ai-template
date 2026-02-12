"""Repository exceptions"""

from app.exceptions import HTTPExceptionMixin


class RepositoryError(HTTPExceptionMixin):
    """Base repository error"""

    detail = "Repository error"
    error_code = "repository_error"
    status_code = 500


class NotFoundError(RepositoryError):
    """Repository not found error"""

    detail = "Item not found"
    error_code = "not_found"
    status_code = 404


class DuplicateError(RepositoryError):
    """Item already exists in the repository"""

    detail = "Item already exists"
    error_code = "duplicate_item"
    status_code = 400


class ReferencedError(RepositoryError):
    """Item is referenced by other items"""

    detail = "Item is referenced by other items"
    error_code = "referenced_item"
    status_code = 400
