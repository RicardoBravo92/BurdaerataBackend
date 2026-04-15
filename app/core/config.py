from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = ""
    API_V1_STR: str = "/api/v1"

    CLERK_SECRET_KEY: str = ""
    AUTHORIZED_PARTIES: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()
