"""Configuration to use in the app"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    APP_NAME: str = Field(default="backend")
    DEBUG_MODE: bool = Field(default=False)
    MAX_ALLOWED_MATCHES: int = Field(default=50)
    ENVIRONMENT: str = Field(default="local")


class DatabaseSettings(BaseSettings):
    DB_NAME: str = Field(default="backend")
    DB_URL: str = Field(default="sqlite:///sql.db")
    ALEMBIC_DATABASE_URL: str | None = Field(default=None)
    DB_POOL_SIZE: int = Field(default=100)
    DB_POOL_PRE_PING: bool = Field(default=False)
    REPOSITORY_NAME: str = Field(default="SQL")  ## For the new entities


class CORSSettings(BaseSettings):
    FRONTEND_URL: str = Field(default="http://localhost:3000")


class OAuthSettings(BaseSettings):
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/oauth/google/callback"
    GOOGLE_USER_INFO_URL: str = "https://www.googleapis.com/oauth2/v1/userinfo"


class CredentialsSettings(BaseSettings):
    """Credentials to use in the app for various services"""

    AUTH_JWT_SECRET: str = ""

    AXIOM_API_KEY: str = ""
    AXIOM_ORG_ID: str = ""
    AXIOM_DATASET_NAME: str = "backend"

    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.0


class AWSSettings(BaseSettings):
    ASSETS_BUCKET: str = ""
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    REGION_NAME: str = "us-east-1"
    ENDPOINT_URL: str | None = None


class LimiterSettings(BaseSettings):
    RATE_LIMIT_REDIS_URL: str | None = None
    RATE_LIMIT_PREFIX: str = "fastapi-limiter"


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="console")  # "console" or "json"
    VERSION: str | None = Field(default=None)
    COMMIT_HASH: str | None = Field(default=None)
    INSTANCE_ID: str | None = Field(default=None)


class Settings(
    CommonSettings,
    CredentialsSettings,
    AWSSettings,
    DatabaseSettings,
    CORSSettings,
    OAuthSettings,
    LimiterSettings,
    LoggingSettings,
):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
