from fastapi import APIRouter, HTTPException, status, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import json

from app.auth.auth import verify_token
from app.db.db import engine, validate_table_exists, load_sql
from app.models.objects import (ObjectCreateRequest,
                                ObjectCreateResponse,
                                PatchObjectRequest,
                                PatchObjectResponse,
                                DeleteObjectResponse)
from app.logger import db_logger


router = APIRouter()


@router.post(
    "/{db_name}/objects", response_model=ObjectCreateResponse, dependencies=[Depends(verify_token)]
)
async def create_object(payload: ObjectCreateRequest,
                        db_name: str = Depends(validate_table_exists),) -> ObjectCreateResponse:
    """
    Create a new object of a given term type with specified attributes.

    Args:
        payload: ObjectCreateRequest containing the type ID, parent ID, and attributes (attrs).

    Returns:
        ObjectCreateResponse: Object metadata and optional warning message.

    Raises:
        HTTPException: For invalid parameters or unexpected DB errors.
    """
    query = text(
        """
        SELECT * FROM post_objects(:db, :up, :type, :attrs)
        """
    )

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                query,
                {
                    "db": db_name,
                    "up": payload.up,
                    "type": payload.id,
                    "attrs": json.dumps(payload.attrs),
                },
            )
            row = result.fetchone()

        if not row:
            db_logger.exception(
                f"Empty response from post_objects: id={payload.id}, up={payload.up}, attrs_keys={list(payload.attrs.keys())}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        obj_id, res = row

        if res == "1":
            return JSONResponse(ObjectCreateResponse(
                id=obj_id,
                up=payload.up,
                t=payload.id,
                val=payload.attrs[f"t{payload.id}"],
            ).model_dump(exclude_none=True))


        if res == "err_non_unique_val":
            return ObjectCreateResponse(
                id=obj_id,
                up=payload.up,
                t=payload.id,
                val=payload.attrs[f"t{payload.id}"],
                warning=res.upper(),
            )

        if res.startswith("err_type_not_found") or res.startswith("err_invalid_ref"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.upper(),
            )

        if res == "err_empty_val":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=res.upper(),
            )

        db_logger.exception(
            f"Unexpected response from post_objects: res='{res}', id={payload.id}, up={payload.up}, attrs_keys={list(payload.attrs.keys())}"
        )


        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except SQLAlchemyError as _e:
        db_logger.exception(f"Database error while executing post_object: {_e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.patch(
    "/{db_name}/objects/{object_id}",
    response_model=PatchObjectResponse,
    dependencies=[Depends(verify_token)],
)
async def patch_object(
    object_id: int = Path(..., description="ID of the object to patch"),
    payload: PatchObjectRequest = ...,
    db_name: str = Depends(validate_table_exists),
):
    """
    Updates an object via patch_object stored procedure.

    Args:
        object_id (int): ID of the object.
        payload (PatchObjectRequest): Dictionary of fields to update in t{id} format.
        db_name (str): Name of the table (validated).

    Returns:
        PatchObjectResponse: Update result with warnings or errors if any.
    """
    print("RAW PAYLOAD:", payload)
    print("EXTRA:", payload.__pydantic_extra__)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT patch_object(:db, :id, :attrs)"),
                {
                    "db": db_name,
                    "id": object_id,
                    "attrs": json.dumps(payload.get_payload(), ensure_ascii=False),
                },
            )
            row = result.scalar_one_or_none()

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error")

    response = {"id": object_id, "val": next(iter(payload.get_payload().values()), None)}

    error_map = {
        "warn_record_exists": ("warnings", "The record already exists"),
        "err_non_unique_val": ("error", "Value is not unique"),
        "err_empty_val": ("error", "Empty value"),
        "err_invalid_ref": ("error", "Invalid reference"),
    }

    for key in error_map:
        if row and row.startswith(key):
            field, message = error_map[key]
            response[field] = message
            break

    return JSONResponse(PatchObjectResponse(**response).model_dump(exclude_none=True))

@router.delete(
    "/{db_name}/objects/{object_id}",
    response_model=DeleteObjectResponse,
    dependencies=[Depends(verify_token)],
)
async def delete_object(
    db_name: str = Path(..., description="Database name"),
    object_id: int = Path(..., description="ID of the object to delete"),
):
    """
    Deletes an object and its nested records recursively.
    Validates references and ensures the object is not metadata.
    """
    async with engine.begin() as conn:
        sql = text("SELECT delete_object(:db, :id)")
        result = await conn.execute(sql, {"db": db_name, "id": object_id})
        res = result.scalar_one_or_none()

        if res is None:
            raise HTTPException(status_code=500, detail="Unexpected DB error")

        if res == "err_obj_not_found":
            raise HTTPException(status_code=404, detail="Object not found")
        if res == "err_is_metadata":
            raise HTTPException(status_code=400, detail="Cannot delete metadata object")
        if res.startswith("err_is_referenced"):
            count = res.split(" ")[1] if " " in res else "unknown"
            raise HTTPException(
                status_code=400,
                detail=f"Object is referenced ({count})"
            )
        if res != "1":
            raise HTTPException(status_code=400, detail=f"Unknown error: {res}")

        return DeleteObjectResponse(id=object_id)
    

@router.get(
    "/{db_name}/objects/{object_id}",
    dependencies=[Depends(verify_token)]
)
async def get_object(
    db_name: str = Depends(validate_table_exists),
    object_id: int = Path(..., description="Object ID to fetch"),
):
    """
    Fetches a specific object and its requisites by ID.

    Returns:
        {
            "id": 252,
            "val": "Yuri",
            "t": 32,
            "up": 1,
            "typ_name": "User",
            "base_typ": 3,
            "reqs": {
                "307": {
                    "type": "ГОСБ",
                    "value": "359"
                },
                ...
            }
        }
    """
    async with engine.connect() as conn:
        sql_obj = load_sql("get_object.sql", db=db_name)
        result = await conn.execute(text(sql_obj), {"object_id": object_id})
        obj_row = result.mappings().fetchone()
        if not obj_row:
            raise HTTPException(status_code=404, detail=f"Object {object_id} not found")

        obj = dict(obj_row)
        term_type = obj["t"]

        sql_reqs = text(load_sql("get_object_requisites.sql", db=db_name))
        result = await conn.execute(sql_reqs, {
            "object_id": object_id,
            "type_id": term_type
        })
        rows = result.mappings().all()
        print("ROWS:", rows)
        reqs = {}
        for row in rows:
            req_id = str(row["req_id"])
            if req_id == "0":
                continue
            reqs[req_id] = {
                "type": row["ref_val"],
                "value": row["ref_t"] if row["ref_t"] else row["req_val"]
            }

        obj["reqs"] = reqs
        return JSONResponse(obj)
