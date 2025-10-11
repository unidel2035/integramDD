from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    BOOLEAN_MODIFIERS: list[str] = ["NOT NULL", "ORDER", "MULTIPLE", "UNIQUE"]
    SQL_DIR: Path = Path(__file__).parent / "sql"

    # Rate limiting settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_CREATE: str = "10/minute"
    RATE_LIMIT_UPDATE: str = "20/minute"
    RATE_LIMIT_DELETE: str = "10/minute"

    # Request size limits (in bytes)
    MAX_REQUEST_SIZE: int = 1_000_000  # 1MB

    # Database connection settings
    DB_POOL_TIMEOUT: int = 30
    DB_COMMAND_TIMEOUT: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
