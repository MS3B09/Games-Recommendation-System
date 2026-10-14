"""Explicit server settings; secret values stay masked and out of API schemas."""

import os
from pathlib import Path
from typing import Self

from dotenv import dotenv_values
from pydantic import BaseModel, SecretStr


class Settings(BaseModel):
    database_url: SecretStr = SecretStr("")
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")

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
        return cls(database_url=SecretStr(url), allowed_origins=explicit_origins)
