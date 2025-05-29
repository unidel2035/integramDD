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

    class Config:
        env_file = ".env"

settings = Settings()
