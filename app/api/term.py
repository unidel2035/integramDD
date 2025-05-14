from fastapi import APIRouter, Path, HTTPException, Depends
from sqlalchemy import text
from typing import List

from app.db.db import engine, load_sql
from app.models.term import TermMetadata
from app.services.term_builder import build_terms_from_rows
from app.auth.auth import verify_token


router = APIRouter()


@router.get("/term", response_model=List[TermMetadata], dependencies=[Depends(verify_token)])
async def get_all_terms():
    sql = load_sql("get_term.sql", filter_clause="")
    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        rows = result.mappings().all()

    return build_terms_from_rows(rows)


@router.get("/term/{term_id}", response_model=TermMetadata, dependencies=[Depends(verify_token)])
async def get_term_by_id(term_id: int = Path(..., description="ID термина")):
    sql = load_sql("get_term.sql", filter_clause="AND obj.id = :term_id")
    async with engine.connect() as conn:
        result = await conn.execute(text(sql), {"term_id": term_id})
        rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    return build_terms_from_rows(rows)[0]
