from fastapi import APIRouter, HTTPException, status, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text, bindparam, String, Integer, JSON
from sqlalchemy.exc import SQLAlchemyError
import json

from app.db.db import engine, validate_table_exists, load_sql
from app.models.objects import *
from app.logger import setup_logger
from app.services.ErrorManager import error_manager as em


router = APIRouter()
logger = setup_logger(__name__)


@router.post(
    "/{db_name}/objects",
    response_model=ObjectCreateResponse,
)
async def create_object(
    payload: ObjectCreateRequest,
    db_name: str = Depends(validate_table_exists),
) -> ObjectCreateResponse:
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
        logger.info(
            f"Creating object with payload: {payload.model_dump(exclude_none=True)}"
        )
        logger.info(f"json dump attrs: {json.dumps(payload.attrs)}")
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
        logger.info(f"DB response: {row}")
        if not row:
            logger.exception(
                f"Empty response from post_objects: id={payload.id}, up={payload.up}, attrs_keys={list(payload.attrs.keys())}"
            )
            raise HTTPException(status_code=500, detail="Empty DB response")

        obj_id, res = row

        if res == "1":
            return JSONResponse(
                ObjectCreateResponse(
                    id=obj_id,
                    up=payload.up,
                    t=payload.id,
                    val=payload.attrs.get(f"t{payload.id}"),
                ).model_dump(exclude_none=True)
            )

        status_code, message = em.get_status_and_message(res) or (None, None)

        if status_code == 200:
            return ObjectCreateResponse(
                id=obj_id,
                up=payload.up,
                t=payload.id,
                val=payload.attrs.get(f"t{payload.id}"),
                warning=message,
            )

        if status_code:
            em.raise_if_error(
                res, log_context=f"POST object t={payload.id} in {db_name}"
            )

        logger.exception(
            f"Unexpected response from post_objects: res='{res}', id={payload.id}, up={payload.up}, attrs_keys={list(payload.attrs.keys())}"
        )
        raise HTTPException(status_code=500, detail="Unexpected database response")

    except SQLAlchemyError as e:
        logger.exception(f"Database error while executing post_object: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.patch(
    "/{db_name}/objects/{object_id}",
    response_model=PatchObjectResponse,
)
async def patch_object(
    object_id: int = Path(..., description="ID of the object to patch"),
    payload: PatchObjectRequest = ...,
    db_name: str = Depends(validate_table_exists),
):
    """
    Updates the object along with its attributes.

    Args:
        object_id (int): ID of the object.
        payload (PatchObjectRequest): Set of fields to update named like t{id}, where {id} is the field (attribute) ID.
        db_name (str): Name of the table (validated).

    Returns:
        PatchObjectResponse: Update result with warnings or errors if any.
    """
    attrs = payload.get_payload()

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT patch_object(:db, :id, :attrs)"),
                {
                    "db": db_name,
                    "id": object_id,
                    "attrs": json.dumps(attrs, ensure_ascii=False),
                },
            )
            res = result.scalar_one_or_none()

    except SQLAlchemyError as e:
        logger.exception(f"DB error while patching object {object_id} in {db_name}")
        raise HTTPException(status_code=500, detail="Database error")

    if res is None:
        logger.warning(f"PATCH failed: no response from DB for object_id={object_id}")
        raise HTTPException(status_code=500, detail="Empty DB response")

    val = list(attrs.values())[0] if len(attrs) == 1 else None

    response = PatchObjectResponse(id=object_id, val=val)

    status_code, message = em.get_status_and_message(res) or (None, None)

    if status_code == 200:
        response.warning = message
    elif status_code:
        em.raise_if_error(res, log_context=f"PATCH object {object_id} in {db_name}")

    return JSONResponse(response.model_dump(exclude_none=True))


@router.delete(
    "/{db_name}/objects/{object_id}",
    response_model=DeleteObjectResponse,
)
async def delete_object(
    db_name: str = Path(..., description="Database name"),
    object_id: int = Path(..., description="ID of the object to delete"),
):
    """
    Deletes an object and its nested records recursively.
    Validates references and ensures the object is not metadata.
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT delete_object(:db, :id)"),
                {"db": db_name, "id": object_id},
            )
            res = result.scalar_one_or_none()

    except SQLAlchemyError as e:
        logger.exception(f"DB error during DELETE object {object_id} in {db_name}")
        raise HTTPException(status_code=500, detail="Database error")

    if res is None:
        logger.error(f"DELETE returned NULL for object_id={object_id}")
        raise HTTPException(status_code=500, detail="Unexpected DB error")

    if res != "1":
        em.raise_if_error(res, log_context=f"DELETE object {object_id} in {db_name}")

    return DeleteObjectResponse(id=object_id)


@router.get("/{db_name}/object/{object_id}")
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
    try:
        async with engine.connect() as conn:
            sql_obj = text(load_sql("get_object.sql", db=db_name))
            result = await conn.execute(sql_obj, {"object_id": object_id})
            obj_row = result.mappings().fetchone()

            if not obj_row:
                logger.info(f"Object {object_id} not found in DB {db_name}")
                raise HTTPException(
                    status_code=404, detail=f"Object {object_id} not found"
                )

            obj = dict(obj_row)
            term_type = obj["t"]

            sql_reqs = text(load_sql("get_object_requisites.sql", db=db_name))
            result = await conn.execute(
                sql_reqs, {"object_id": object_id, "type_id": term_type}
            )
            rows = result.mappings().all()

            reqs = {}
            for row in rows:
                req_id = str(row["req_id"])
                if req_id == "0":
                    continue

                value = row["ref_t"] if row["ref_t"] is not None else row["req_val"]
                reqs[req_id] = {
                    "type": row["ref_val"],
                    "value": value,
                }

            obj["reqs"] = reqs
            return JSONResponse(obj)

    except SQLAlchemyError as e:
        logger.exception(f"DB error while fetching object {object_id} in {db_name}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/{db_name}/objects/{term_id}", response_model=TermObjectsResponse)
async def get_term_objects(
    db_name: str = Path(..., description="Database name"),
    term_id: int = Path(..., description="ID of the term"),
    parent_id: int = Query(1, alias="up", description="Parent ID"),
):
    """
    Returns:
        {
            "t": 32,
            "name": "User",
            "base": 3,
            "header": [...],
            "objects": [...]
        }
    """
    try:
        async with engine.connect() as conn:
            # --- Get metadata
            meta_sql = text(
                load_sql("get_term_metadata.sql", db=db_name, term_id=term_id)
            )
            meta_rows = (await conn.execute(meta_sql)).fetchall()
            if not meta_rows:
                raise HTTPException(status_code=404, detail="Term not found")

            # --- Get object list
            objs_sql = text(
                load_sql(
                    "get_term_objects.sql",
                    db=db_name,
                    term_id=term_id,
                    parent_id=parent_id,
                )
            )
            object_rows = (await conn.execute(objs_sql)).fetchall()

            # --- Build header
            header_map = {}
            header = []
            for row in meta_rows:
                logger.info(f"Processing header row: {row._asdict()}")
                if row.req_id not in header_map:
                    field = HeaderField(
                        id=row.req_id,
                        t=row.req_t,
                        name=row.req_val,
                        base=row.base,
                        ref=row.ref_id,
                        is_table_req=row.is_table_req,
                        modifiers=[m for m in (row.mods or [])],
                        original_name=row.ref_val,
                    )
                    header.append(field)
                    header_map[row.req_id] = field

            # --- Detect tabular requisites with ORDER
            table_reqs = dict(
                (field.t, field) for field in header if field.is_table_req
            )

            ordered_table_reqs = dict(
                (field.t, field)
                for field in table_reqs.values()
                if any("ORDER" in mod for mod in field.modifiers) and field.is_table_req
            )

            # --- Load SQL templates
            reqs_template = load_sql(
                "get_object_reqs.sql", db=db_name, obj_id=":obj_id"
            )

            agg_template = load_sql(
                "get_object_table_reqs.sql",
                db=db_name,
                not_in_clause="NOT",
                obj_id=":obj_id",
                array_ids=":array_ids",
            )
            agg_ordered_template = load_sql(
                "get_object_table_reqs.sql",
                db=db_name,
                not_in_clause="",
                obj_id=":obj_id",
                array_ids=":array_ids",
            )

            objects = []
            ordered_req_map = {}
            logger.info(f"Ordered table requisites: {ordered_table_reqs}")
            for obj in object_rows:
                if ordered_table_reqs:
                    array_ids = ",".join(map(str, ordered_table_reqs))
                    ordered_reqs_sql_text = agg_ordered_template.replace(
                        ":obj_id", str(obj.id)
                    ).replace(":array_ids", array_ids)
                    logger.info(
                        f"Using aggregated SQL for object {obj.id} with array_ids: {array_ids}"
                    )
                    ordered_reqs = text(ordered_reqs_sql_text)

                    ordered_reqs_rows = (await conn.execute(ordered_reqs)).fetchall()
                    for row in ordered_reqs_rows:
                        ordered_req_map[row[1]] = row[3]
                    
                    logger.info(f"Ordered requisites rows: {ordered_reqs_rows}")
                    

                reqs_sql_text = reqs_template.replace(":obj_id", str(obj.id))
                reqs_sql = text(reqs_sql_text)

                reqs_rows = (await conn.execute(reqs_sql)).fetchall()

                row_data = {}
                for req_row in reqs_rows:
                    logger.info(f"Processing req_row: {req_row}")
                    req_id = req_row[1]
                    field = header_map.get(req_id)

                    val = req_row[0]
                    logger.info(f"Value for req_id {req_id}: {val}")
                    logger.info(f"Field for req_id {req_id}: {field}")
                    if field:
                        if field.ref:
                            row_data[str(field.ref)] = val
                        else:
                            row_data[field.name] = val
                    else:
                        # Проверяем, есть ли req_id среди значений .t в header_map
                        if any(
                            getattr(h, "t", None) == req_id for h in header_map.values()
                        ):
                            if row_data.get(f"{req_row[2]}") is None:
                                row_data[f"{req_row[2]}"] = {"vals": [req_row[0]]}
                            else:
                                row_data[f"{req_row[2]}"]["vals"].append(req_row[0])
                            
                            if req_id in ordered_table_reqs.keys():
                                row_data[f"{req_row[2]}"]["q"] = ordered_req_map.get(
                                    req_id, None
                                )
                        elif (
                            len(req_row) > 3
                            and req_row[3]
                            and str(req_row[3]).isdigit()
                        ):
                            row_data[f"{req_row[2]}"] = str((req_row[3]))

                logger.info(f"Row data for object {obj.id}: {row_data}")
                objects.append(
                    ObjectRow(
                        id=obj.id,
                        up=obj.up,
                        val=obj.val,
                        reqs=row_data,
                    )
                )
                logger.info(f"Added object: {objects[-1]}")
            
            logger.info(f"Header map: {header_map}")

            response = TermObjectsResponse(
                t=meta_rows[0].id,
                name=meta_rows[0].obj,
                base=meta_rows[0].base,
                header=header,
                objects=objects,
            )
            return JSONResponse(response.model_dump(exclude_none=True))

    except SQLAlchemyError:
        logger.exception(f"DB error while fetching term {term_id} in {db_name}")
        raise HTTPException(status_code=500, detail="Database error")
