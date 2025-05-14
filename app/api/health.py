from fastapi import APIRouter
from app.db.db import engine
from sqlalchemy import text

router = APIRouter()

async def check_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

@router.get("/health")
async def health_check():
    return await check_db()
