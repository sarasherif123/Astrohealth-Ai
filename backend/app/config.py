from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_DB_PATH = (BACKEND_ROOT / "astrohealth.db").as_posix()


class Settings(BaseSettings):
    PROJECT_NAME: str = "AstroHealth AI"
    ENV: str = "development"  # "development" | "production"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

    JWT_SECRET_KEY: str = "dev-only-mars-transit-jwt-secret-override-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MISSION_HMAC_SECRET: str = "dev-only-mission-control-hmac-secret-2026"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_GENERATION_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    DATA_DIR: Path = DEFAULT_DATA_DIR
    NASA_KB_DIR: Path = DEFAULT_DATA_DIR / "nasa_kb"
    KB_INDEX_PATH: Path = DEFAULT_DATA_DIR / "kb_index.json"
    CATALOG_PATH: Path = DEFAULT_DATA_DIR / "countermeasure_catalog.json"
    FRONTEND_PUBLIC_DIR: Path = BACKEND_ROOT.parent / "frontend" / "public"

    MAX_TELEMETRY_ROWS_PER_USER: int = 1000

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENV.lower() == "production":
            if "dev-only" in self.JWT_SECRET_KEY or "dev-only" in self.MISSION_HMAC_SECRET:
                raise ValueError(
                    "FATAL: Default JWT_SECRET_KEY or MISSION_HMAC_SECRET cannot be used when ENV=production."
                )
        return self


settings = Settings()
