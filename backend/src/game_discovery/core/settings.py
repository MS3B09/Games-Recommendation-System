"""Explicit server settings; secret values stay masked and out of API schemas."""

import os
from pathlib import Path
from typing import Self

from dotenv import dotenv_values
from pydantic import BaseModel, Field, SecretStr


class Settings(BaseModel):
    database_url: SecretStr = SecretStr("")
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    query_tokenizer_path: str = ""
    query_model_path: str = ""
    query_artifact_path: str = ""
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = Field(default="llama-3.3-70b-versatile", min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_./-]+$")
    ai_enabled: bool = False
    ai_daily_calls: int = Field(default=50, ge=1, le=100)
    ai_daily_tokens: int = Field(default=500000, ge=1, le=1500000)

    @classmethod
    def from_environment(cls) -> Self:
        default_file = Path(__file__).resolve().parents[3] / ".env"
        path = Path(os.environ.get("GAME_DISCOVERY_ENV_FILE", str(default_file)))
        file_values = dotenv_values(path, interpolate=False) if path.is_file() else {}
        url = os.environ.get("DATABASE_URL", file_values.get("DATABASE_URL") or "")
        origins = os.environ.get("ALLOWED_ORIGINS", file_values.get("ALLOWED_ORIGINS") or "http://localhost:5173,http://127.0.0.1:5173")
        explicit_origins = tuple(value.strip() for value in origins.split(",") if value.strip())
        if "*" in explicit_origins:
            raise ValueError("Explicit frontend origins are required")
        encoder = {key: os.environ.get(key.upper(), file_values.get(key.upper()) or "")
                   for key in ("query_tokenizer_path", "query_model_path", "query_artifact_path")}
        values: dict[str, object] = {"database_url": url, "allowed_origins": explicit_origins, **encoder}
        for name in ("groq_api_key", "groq_model", "ai_enabled", "ai_daily_calls", "ai_daily_tokens"):
            value = os.environ.get(name.upper(), file_values.get(name.upper()))
            if value:
                values[name] = value
        return cls.model_validate(values)
