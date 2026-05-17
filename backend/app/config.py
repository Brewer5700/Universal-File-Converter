from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    max_upload_mb: int
    max_workers: int
    api_key: str | None
    allow_public: bool
    allowed_origins: list[str]
    log_level: str


    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def _default_origins() -> list[str]:
    return [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ]


def load_settings() -> Settings:
    data_dir = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
    if allowed_origins_env:
        allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    else:
        allowed_origins = _default_origins()

    api_key = os.getenv("API_KEY")
    api_key = api_key.strip() if api_key else None

    return Settings(
        data_dir=data_dir,
        max_upload_mb=_env_int("MAX_UPLOAD_MB", 200),
        max_workers=_env_int("MAX_WORKERS", 4),
        api_key=api_key,
        allow_public=_env_bool("ALLOW_PUBLIC", False),
        allowed_origins=allowed_origins,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = load_settings()
