from fastapi import APIRouter
from sqlalchemy import text
from pydantic import BaseModel

from app.db.db import engine
from app.logger import setup_logger

router = APIRouter()
logger = setup_logger()


class HealthStatus(BaseModel):
    status: str
    db: str


async def check_database_connection() -> HealthStatus:
    """Performs a simple health check of the database connection.

    Executes a lightweight `SELECT 1` query to ensure the DB is reachable.

    Returns:
        dict: A dictionary with status and database connection info.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return HealthStatus(status="ok", db="connected")
    except Exception as e:
        logger.exception(f"Database health check failed: {e}")
        return HealthStatus(status="error", db="unreachable")


@router.get("/health", response_model=HealthStatus)
async def health_check() -> dict:
    """Health check endpoint.

    Verifies the health of the service and its connection to the database.

    Returns:
        dict: Service and DB status.
    """
    return await check_database_connection()
