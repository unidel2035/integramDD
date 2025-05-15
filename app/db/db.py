"""Database engine and session management for async PostgreSQL operations."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.settings import settings
from pathlib import Path


# Construct the async PostgreSQL database URL
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Create async SQLAlchemy engine and session factory
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Yields an async database session (used as a FastAPI dependency)."""
    async with SessionLocal() as session:
        yield session


def load_sql(name: str, **replacements) -> str:
    """Loads a .sql file and formats it with optional replacements.

    Args:
        name (str): The name of the SQL file (relative to the configured SQL_DIR).
        **replacements: Optional keyword arguments to substitute in the SQL via str.format.

    Returns:
        str: The formatted SQL query string.
    """
    sql_path: Path = settings.SQL_DIR / name
    content: str = sql_path.read_text(encoding="utf-8")
    return content.format(**replacements)
