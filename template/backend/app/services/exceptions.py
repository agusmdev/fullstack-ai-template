from app.exceptions import HTTPExceptionMixin


class ExternalApiException(HTTPExceptionMixin):
    """Base external API exception"""

    detail = "External API error"
    error_code = "external_api_error"
    status_code = 500
