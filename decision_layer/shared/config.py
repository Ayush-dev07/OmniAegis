from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, AnyUrl, Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    redis_url: RedisDsn = Field(..., alias="REDIS_URL")
    database_url: PostgresDsn = Field(..., alias="DATABASE_URL")

    neo4j_uri: AnyUrl = Field(..., alias="NEO4J_URI")
    neo4j_username: str = Field(..., alias="NEO4J_USERNAME", min_length=1)
    neo4j_password: SecretStr = Field(..., alias="NEO4J_PASSWORD")

    grafana_prometheus_url: AnyHttpUrl = Field(..., alias="GRAFANA_PROMETHEUS_URL")
    grafana_api_key: SecretStr = Field(..., alias="GRAFANA_API_KEY")

    pinata_api_key: SecretStr = Field(..., alias="PINATA_API_KEY")
    web3_provider_url: AnyUrl = Field(..., alias="WEB3_PROVIDER_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance for the current process."""

    return Settings()


settings = get_settings()
