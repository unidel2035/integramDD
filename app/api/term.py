from fastapi import APIRouter, Path, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import json

from app.db.db import engine, load_sql, validate_table_exists
from app.models.term import TermMetadata, TermCreateRequest, TermCreateResponse
from app.services.term_builder import build_terms_from_rows
from app.auth.auth import verify_token
from app.logger import db_logger


router = APIRouter()


@router.get(
    "/{db_name}/metadata",
    response_model=List[TermMetadata],
    dependencies=[Depends(verify_token)],
)
async def get_all_terms(
    db_name: str = Depends(validate_table_exists),
):
    """Fetches all metadata terms from the database.

    This endpoint returns a list of all defined terms and their metadata.
    Authorization is required.

    Returns:
        List[TermMetadata]: A list of term metadata entries.
    """
    sql = load_sql("get_term.sql", db=db_name, filter_clause="")

    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        rows = result.mappings().all()

    return JSONResponse(build_terms_from_rows(rows))


@router.get(
    "/{db_name}/metadata/{term_id}",
    response_model=TermMetadata,
    dependencies=[Depends(verify_token)],
)
async def get_term_by_id(
    term_id: int = Path(..., description="Term ID to fetch"),
    db_name: str = Depends(validate_table_exists),
):
    """Fetches metadata for a specific term by its ID.

    This endpoint retrieves detailed metadata for a single term,
    including its attributes and modifiers. Returns 404 if the term is not found.
    Authorization is required.

    Args:
        term_id (int): ID of the term to retrieve.

    Returns:
        TermMetadata: Metadata of the specified term.

    Raises:
        HTTPException: If the term with given ID does not exist.
    """
    sql = load_sql("get_term.sql", db=db_name, filter_clause="AND obj.id = :term_id")

    async with engine.connect() as conn:
        result = await conn.execute(text(sql), {"term_id": term_id})
        rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    return JSONResponse(build_terms_from_rows(rows)[0])


@router.post(
    "/{db_name}/metadata", response_model=TermCreateResponse, dependencies=[Depends(verify_token)]
)
async def create_term(payload: TermCreateRequest, db_name: str = Depends(validate_table_exists),) -> TermCreateResponse:
    """Create a new term or return an existing one if it already exists.

    Executes the `post_terms` stored procedure with provided parameters.

    Args:
        payload: Request body containing term value, base type, and optional modifiers.

    Returns:
        TermCreateResponse: JSON response with term metadata and optional warning.

    Raises:
        HTTPException: 400 if response is unexpected, 500 if DB call fails.
    """
    query = text(
        """
        SELECT * FROM post_terms(:db, :value, :base, :mods)
    """
    )

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                query,
                {
                    "db": db_name,
                    "value": payload.val,
                    "base": payload.t,
                    "mods": json.dumps(payload.mods or {}),
                },
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        term_id, result_flag = row

        if result_flag == "1":
            return TermCreateResponse(id=term_id, t=payload.t, val=payload.val)

        if result_flag == "warn_term_exists":
            return TermCreateResponse(
                id=term_id, t=payload.t, val=payload.val, warnings="Term already exists"
            )

        db_logger.exception(f"Unexpected result from post_terms: {result_flag}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except SQLAlchemyError as _e:
        db_logger.exception(f"Database error while executing post_terms: {_e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
