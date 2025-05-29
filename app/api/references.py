from fastapi import APIRouter, Depends, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy import text
import json

from app.auth.auth import verify_token
from app.db.db import engine, validate_table_exists
from app.models.references import (
    CreateReferenceRequest,
    CreateReferenceResponse,
)

router = APIRouter()

@router.post(
    "/{db_name}/references",
    response_model=CreateReferenceResponse,
    dependencies=[Depends(verify_token)],
)
async def create_reference(
    db_name: str = Depends(validate_table_exists),
    payload: CreateReferenceRequest = ...,
):
    """
    Creates a reference to a term (object with val = NULL and t = term_id).
    If such reference already exists, its ID is returned with a warning.
    
    Returns:
        JSON containing ID of created or existing reference.
    """
    sql = text("SELECT * FROM post_references(:db, :term_id)")

    async with engine.begin() as conn:  # type: AsyncConnection
        result = await conn.execute(sql, {
            "db": db_name,
            "term_id": payload.id
        })
        row = result.mappings().fetchone()

    if not row or row["res"] is None:
        return JSONResponse(status_code=400, content={"errors": "Unknown error during reference creation."})

    response = CreateReferenceResponse(id=row["newid"])

    if row["res"] == "warn_ref_exists":
        response.warnings = "Reference already exists"
    elif row["res"] == "err_incorrect_term":
        response.errors = "Incorrect term ID"
    elif row["res"] != "1":
        response.errors = f"Unexpected error: {row['res']}"

    return response