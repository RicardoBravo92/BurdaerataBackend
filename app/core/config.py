from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # App
    app_name: str = "Burdaerata API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database (required)
    database_url: str = Field(validation_alias="DATABASE_URL")

    # Clerk Auth
    clerk_secret_key: str = Field(validation_alias="CLERK_SECRET_KEY")
    authorized_parties_raw: str = Field(
        default="http://localhost:3000",
        validation_alias="AUTHORIZED_PARTIES",
    )

    # Email
    resend_api_key: str = Field(default="", validation_alias="RESEND_API_KEY")

    # CORS
    allowed_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: list[str] = ["Authorization", "Content-Type"]
    allow_credentials: bool = True

    @computed_field
    @property
    def authorized_parties(self) -> list[str]:
        """Parse comma-separated AUTHORIZED_PARTIES into list[str]."""
        raw = self.authorized_parties_raw
        if not raw:
            return ["http://localhost:3000"]
        return [p.strip() for p in raw.split(",") if p.strip()]


settings = Settings()