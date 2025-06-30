from fastapi import APIRouter, Depends, Path, Body, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import json

from app.auth.auth import verify_token
from app.db.db import engine, validate_table_exists
from app.models.requisites import (
    AddRequisitePayload,
    AddRequisiteResponse,
    RequisiteModifiers,
)
from app.services.error_manager import error_manager as em
from app.logger import setup_logger


router = APIRouter()
logger = setup_logger(__name__)

@router.post(
    "/{db_name}/requisites",
    response_model=AddRequisiteResponse,
)
async def post_requisite(
    db_name: str = Depends(validate_table_exists),
    payload: AddRequisitePayload = Body(
        ..., description="Requisite data with optional modifiers"
    ),
):
    """
    Adds a requisite (attribute) to the specified term.
    If the requisite already exists, returns its ID with a warning.
    Modifiers like NOT NULL, UNIQUE and ALIAS can be optionally provided directly in the body.

    Example payload:
    {
        "id": 32,
        "t": 100,
        "unique": 1,
        "notnull": 1,
        "alias": "Position"
    }

    Returns:
        JSON with new requisite ID or existing ID and warning.
    """
    sql = text("SELECT * FROM post_requisites(:db, :term_id, :req_id, :mods)")
    mods_dict = payload.__pydantic_extra__ or {}

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                sql,
                {
                    "db": db_name,
                    "term_id": payload.id,
                    "req_id": payload.t,
                    "mods": json.dumps(mods_dict, ensure_ascii=False),
                },
            )
            row = result.mappings().fetchone()

    except SQLAlchemyError as e:
        logger.exception(f"DB error while posting requisite for term {payload.id}")
        raise HTTPException(status_code=500, detail="Database error")

    if not row or row["res"] is None:
        logger.error("post_requisites returned NULL row")
        raise HTTPException(
            status_code=400, detail="Unknown error during requisite creation"
        )

    result_flag = row["res"]
    req_id = row["newid"]

    status_code, msg = em.get_status_and_message(result_flag) or (None, None)

    if status_code == 200:
        return JSONResponse(
            AddRequisiteResponse(id=req_id, warnings=msg).model_dump(exclude_none=True)
        )

    if status_code:
        em.raise_if_error(
            result_flag, log_context=f"POST /requisites term_id={payload.id}"
        )

    if result_flag != "1":
        logger.warning(f"Unexpected result from post_requisites: {result_flag}")
        return JSONResponse(
            AddRequisiteResponse(
                id=req_id, warnings=f"Unexpected result: {result_flag}"
            ).model_dump(exclude_none=True)
        )

    return JSONResponse(AddRequisiteResponse(id=req_id).model_dump(exclude_none=True))
