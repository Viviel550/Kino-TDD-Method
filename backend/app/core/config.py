from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path


def get_settings() -> Settings:
    default = Path(__file__).resolve().parents[2] / "cinema.db"      # backend/cinema.db
    return Settings(db_path=Path(os.environ.get("CINEMA_DB_PATH", default)))
