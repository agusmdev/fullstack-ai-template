# ExternalApiException has moved to app.integrations.http_client.
# This re-export exists for backwards compatibility.
from app.integrations.http_client import ExternalApiException

__all__ = ["ExternalApiException"]
