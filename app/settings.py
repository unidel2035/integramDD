from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "integram"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    SQL_DIR: Path = Path(__file__).parent.parent / "sql"

    class Config:
        env_file = ".env"


settings = Settings()
