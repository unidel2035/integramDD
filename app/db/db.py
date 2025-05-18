"""Database engine and session management for async PostgreSQL operations."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from app.settings import settings
from pathlib import Path
from fastapi import Depends, Path, HTTPException

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


async def validate_table_exists(
    db_name: str = Path(..., description="Target table name"),
    engine: AsyncEngine = Depends(lambda: engine),
) -> str:
    """
    Validates that a table with the given name exists in the current database schema (e.g., 'public').
    Raises 404 error if not found.
    """
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = :table
    """)

    async with engine.begin() as conn:
        result = await conn.execute(query, {"table": db_name})
        if not result.scalar():
            raise HTTPException(status_code=404, detail=f"Table '{db_name}' not found.")

    return db_name
