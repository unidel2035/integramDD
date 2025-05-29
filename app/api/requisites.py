from fastapi import APIRouter, Depends, Path, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Union
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text
import json

from app.auth.auth import verify_token
from app.db.db import engine, validate_table_exists
from app.models.requisites import (
    AddRequisitePayload,
    AddRequisiteResponse,
    RequisiteModifiers,
)


router = APIRouter()


@router.post(
    "/{db_name}/requisites",
    response_model=AddRequisiteResponse,
    dependencies=[Depends(verify_token)],
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

    async with engine.begin() as conn:
        result = await conn.execute(
            sql,
            {
                "db": db_name,
                "term_id": payload.id,
                "req_id": payload.t,
                "mods": json.dumps(mods_dict),
            },
        )
        row = result.mappings().fetchone()

    if not row or row["res"] is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Unknown error during requisite creation."},
        )

    response = AddRequisiteResponse(id=row["newid"])
    if row["res"] == "warn_req_exists":
        response.warnings = "Requisite already exists"
    elif row["res"].startswith("err"):
        return JSONResponse(status_code=400, content={"error": row["res"]})

    return response
