"""Carga de variables de entorno del proyecto."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Configuración mínima necesaria para la capa de datos."""

    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://eldojo_app:eldojo_app_password@127.0.0.1:3306/eldojo_db",
    )


settings = Settings()
