from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth.auth import verify_token
from app.db.db import engine, validate_table_exists
from app.models.references import (
    CreateReferenceRequest,
    CreateReferenceResponse,
)
from app.services.error_manager import error_manager as em
from app.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post(
    "/{db_name}/references",
    response_model=CreateReferenceResponse,
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

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT * FROM post_references(:db, :term_id)"),
                {"db": db_name, "term_id": payload.id},
            )
            row = result.mappings().fetchone()

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error while creating reference to term {payload.id}"
        )
        raise HTTPException(status_code=500, detail="Database error")

    if not row or row["res"] is None:
        logger.error(f"Reference creation failed, no result for term {payload.id}")
        raise HTTPException(
            status_code=400, detail="Unknown error during reference creation"
        )

    result_flag = row["res"]
    ref_id = row["newid"]

    status_code, message = em.get_status_and_message(result_flag) or (None, None)

    if status_code == 200:
        return JSONResponse(
            CreateReferenceResponse(id=ref_id, warnings=message).model_dump(
                exclude_none=True
            ),
            status_code=status_code,
        )

    if status_code:
        em.raise_if_error(
            result_flag, log_context=f"POST /references term_id={payload.id}"
        )

    logger.info(f"Reference creation returned unexpected result: {result_flag}")
    return JSONResponse(
        CreateReferenceResponse(id=ref_id).model_dump(exclude_none=True)
    )
