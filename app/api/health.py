from fastapi import APIRouter
from sqlalchemy import text
from app.db.db import engine

router = APIRouter()


async def check_db() -> dict:
    """Performs a simple health check of the database connection.

    Executes a lightweight `SELECT 1` query to ensure the DB is reachable.

    Returns:
        dict: A dictionary with status and database connection info.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Verifies the health of the service and its connection to the database.

    Returns:
        dict: Service and DB status.
    """
    return await check_db()
