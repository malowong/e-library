from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ELIBRARY_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://elibrary:elibrary@localhost:5432/elibrary"
    jwt_secret: str = "insecure-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60

    max_active_loans: int = 5
    loan_period_days: int = 14


@lru_cache
def get_settings() -> Settings:
    return Settings()
