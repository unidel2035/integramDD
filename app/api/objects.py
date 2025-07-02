from fastapi import APIRouter, HTTPException, status, Depends, Path, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text, bindparam, String, Integer, JSON
from sqlalchemy.exc import SQLAlchemyError
import json

from app.db.db import engine, validate_table_exists, load_sql
from app.models.objects import *
from app.models.filter import FilterQuery
from app.logger import setup_logger
from app.services.error_manager import error_manager as em
from app.services.object_by_term import (
    _build_header,
    _detect_ordered_reqs,
    _fetch_metadata,
    _fetch_objects,
    _fetch_ordered_reqs,
    _build_reqs_map,
)
from app.services.filter_builder import FilterBuilder


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
    
    logger.info(
        f"Patching object {object_id} in {db_name} with attrs: {attrs}"
    )

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
        response.warnings = message
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
    request: Request,
    db_name: str = Path(..., description="Database name"),
    term_id: int = Path(..., description="ID of the term"),
    parent_id: int = Query(1, alias="up", description="Parent ID"),
    filters: FilterQuery = Depends(),
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
        _filters = {k: v for k, v in request.query_params.items()}

        async with engine.connect() as conn:
            meta_rows = await _fetch_metadata(conn, db_name, term_id)
            if not meta_rows:
                raise HTTPException(status_code=404, detail="Term not found")

            header, header_map = _build_header(meta_rows)
            # FILTER
            
            joins = where_clause = ""
            sql_params = {}
            
            if _filters:
                logger.debug(f"Applying filters: {_filters}")
                filter_builder = FilterBuilder(
                    _filters, term_id=term_id, db_name=db_name, term_name=meta_rows[0].obj, header=header
                )
                joins, where_clause, sql_params = filter_builder.build()
                
                logger.debug(f"Generated joins: {joins}")
                logger.debug(f"Generated where clause: {where_clause}")
                logger.debug(f"SQL parameters: {sql_params}")

            object_rows = await _fetch_objects(
                conn,
                db_name,
                term_id,
                parent_id,
                joins=joins,
                where_clause=where_clause,
                limit=filters.limit,
                offset=filters.offset,
                sql_params=sql_params,
            )


            table_reqs, ordered_table_reqs = _detect_ordered_reqs(header)
            logger.debug(f"Ordered table requisites: {ordered_table_reqs}")

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
            for obj in object_rows:
                ordered_req_map = {}
                if ordered_table_reqs:
                    ordered_req_map = await _fetch_ordered_reqs(
                        conn, obj.id, agg_ordered_template, ordered_table_reqs
                    )

                row_data = await _build_reqs_map(
                    conn,
                    obj.id,
                    reqs_template,
                    header_map,
                    ordered_table_reqs,
                    ordered_req_map,
                )

                objects.append(
                    ObjectRow(
                        id=obj.id,
                        up=obj.up,
                        val=obj.val,
                        reqs=row_data,
                    )
                )

            return JSONResponse(
                TermObjectsResponse(
                    t=meta_rows[0].id,
                    name=meta_rows[0].obj,
                    base=meta_rows[0].base,
                    header=header,
                    objects=objects,
                ).model_dump(exclude_none=True)
            )

    except SQLAlchemyError:
        logger.exception(f"DB error while fetching term {term_id} in {db_name}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/{db_name}/objects/graphql")
async def get_term_objects_post(query: ObjectQuery, db_name: str = Path(..., description="Database name")):
    """
    Альтернатива GET-запросу на /objects/{termId}?up={parentId}, но с телом POST.
    """
    term_id = query.term_id
    parent_id = query.up
    limit = query.limit
    offset = query.offset
    filters = query.filters or {}

    async with engine.connect() as conn:
        meta_rows = await _fetch_metadata(conn, db_name=db_name, term_id=term_id)
        if not meta_rows:
            raise HTTPException(status_code=404, detail="Term not found")

        header, header_map = _build_header(meta_rows)

        joins = where_clause = ""
        sql_params = {}

        if filters:
            filter_builder = FilterBuilder(
                filters,
                term_id=term_id,
                db_name=db_name,
                term_name=meta_rows[0].obj,
                header=header,
            )
            joins, where_clause, sql_params = filter_builder.build()

        object_rows = await _fetch_objects(
            conn,
            db_name,
            term_id,
            parent_id,
            joins=joins,
            where_clause=where_clause,
            limit=limit,
            offset=offset,
            sql_params=sql_params,
        )

        table_reqs, ordered_table_reqs = _detect_ordered_reqs(header)

        reqs_template = load_sql("get_object_reqs.sql", db=db_name, obj_id=":obj_id")
        agg_template = load_sql("get_object_table_reqs.sql", db=db_name, not_in_clause="NOT", obj_id=":obj_id", array_ids=":array_ids")
        agg_ordered_template = load_sql("get_object_table_reqs.sql", db=db_name, not_in_clause="", obj_id=":obj_id", array_ids=":array_ids")

        objects = []
        for obj in object_rows:
            ordered_req_map = {}
            if ordered_table_reqs:
                ordered_req_map = await _fetch_ordered_reqs(conn, obj.id, agg_ordered_template, ordered_table_reqs)

            row_data = await _build_reqs_map(
                conn,
                obj.id,
                reqs_template,
                header_map,
                ordered_table_reqs,
                ordered_req_map,
            )

            objects.append(
                ObjectRow(
                    id=obj.id,
                    up=obj.up,
                    val=obj.val,
                    reqs=row_data,
                )
            )

        return JSONResponse(
            TermObjectsResponse(
                t=meta_rows[0].id,
                name=meta_rows[0].obj,
                base=meta_rows[0].base,
                header=header,
                objects=objects,
            ).model_dump(exclude_none=True)
        )