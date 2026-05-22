import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GangaRakshak AI Incident API"
    database_url: str = Field(
        default="sqlite:///./backend/ganga_rakshak.db",
        alias="DATABASE_URL",
    )
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"])
    media_root: str = Field(default="backend/uploads", alias="MEDIA_ROOT")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def normalize_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("["):
                parsed = json.loads(raw)
                return [item.strip() for item in parsed if item.strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
