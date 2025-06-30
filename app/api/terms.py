from fastapi import APIRouter, Path, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text, bindparam
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import json

from app.db.db import engine, load_sql, validate_table_exists
from app.models.terms import *
from app.services.term_builder import build_terms_from_rows
from app.services.error_manager import error_manager as em
from app.auth.auth import verify_token
from app.logger import setup_logger
from app.settings import settings


router = APIRouter()
logger = setup_logger(__name__)


@router.get(
    "/{db_name}/terms",
    response_model=List[Term],
)
async def get_all_terms(
    db_name: str = Depends(validate_table_exists),
):
    """Fetches all metadata terms from the database.

    This endpoint returns a list of all defined terms and.
    Authorization is required.

    Returns:
        List[TermMetadata]: A list of term entries.
    """
    try:
        sql = load_sql("get_terms.sql", db=db_name)

        async with engine.connect() as conn:
            result = await conn.execute(text(sql))
            rows = result.mappings().all()

        return JSONResponse([dict(row) for row in rows])
    except SQLAlchemyError as e:
        logger.exception(f"DB error while fetching terms from {db_name}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get(
    "/{db_name}/terms/{term_id}",
    response_model=Term,
)
async def get_term(
    term_id: int = Path(..., description="Term ID to fetch"),
    db_name: str = Depends(validate_table_exists),
):
    """
    Fetches data for a specific term by ID.

    This endpoint returns data for a single term from the specified database,
    only if it is a top-level term and is not referenced by other objects.
    Authorization is required.

    Args:
        term_id (int): ID of the term to retrieve.
        db_name (str): Database name, validated before execution.

    Returns:
        Term: A dictionary containing the term's ID, value, and base type.
    """
    try:
        sql = load_sql("get_term.sql", db=db_name, term_id=term_id)

        async with engine.connect() as conn:
            result = await conn.execute(text(sql))
            rows = result.mappings().all()
        if not rows:
            raise HTTPException(status_code=404, detail=f"Term {term_id} not found")
        return JSONResponse(dict(rows[0]))
    except SQLAlchemyError as e:
        logger.exception(f"DB error while fetching terms from {db_name}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get(
    "/{db_name}/metadata/{term_id}",
    response_model=TermMetadata,
)
async def get_metadata_by_id(
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
    sql = load_sql(
        "get_metadata.sql", db=db_name, filter_clause="AND obj.id = :term_id"
    )

    async with engine.connect() as conn:
        result = await conn.execute(text(sql), {"term_id": term_id})
        rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    return JSONResponse(build_terms_from_rows(rows)[0])


@router.get(
    "/{db_name}/metadata",
    response_model=List[TermMetadata],
)
async def get_all_metadata(db_name: str = Depends(validate_table_exists)):
    """Fetches all metadata terms from the database.

    This endpoint returns a list of all defined terms and their metadata.
    Authorization is required.

    Returns:
        List[TermMetadata]: A list of term metadata entries.
    """
    sql = load_sql("get_metadata.sql", db=db_name, filter_clause="")

    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        rows = result.mappings().all()

    return JSONResponse(build_terms_from_rows(rows))


@router.post(
    "/{db_name}/terms",
    response_model=TermCreateResponse,
)
async def create_term(
    payload: TermCreateRequest,
    db_name: str = Depends(validate_table_exists),
) -> TermCreateResponse:
    """
    Create a new term or return an existing one if it already exists.
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
                    "mods": json.dumps(
                        payload.mods.get("mods") or {}, ensure_ascii=False
                    ),
                },
            )
            row = result.fetchone()

    except SQLAlchemyError as e:
        logger.exception(f"Database error while executing post_terms: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        logger.error(f"No response from post_terms for value={payload.val}")
        raise HTTPException(status_code=500, detail="Empty DB response")

    term_id, result_flag = row

    # Обработка ошибок и предупреждений через error_manager
    status_code, message = em.get_status_and_message(result_flag) or (None, None)

    if status_code == 200:
        return JSONResponse(
            TermCreateResponse(
                id=term_id,
                t=payload.t,
                val=payload.val,
                warnings=message,
            ).model_dump(exclude_none=True)
        )

    if status_code:
        em.raise_if_error(result_flag, log_context=f"POST /terms {payload.val}")

    logger.exception(f"Unexpected result from post_terms: {result_flag}")
    raise HTTPException(status_code=500, detail="Unexpected DB response")


@router.patch(
    "/{db_name}/terms/{term_id}",
    response_model=PatchTermResponse,
)
async def patch_term(
    db_name: str = Path(..., description="Database name"),
    term_id: int = Path(..., description="ID of the term to update"),
    payload: PatchTermRequest = ...,
):
    """
    Updates the name or base type of a term. If a term with the same name already exists,
    returns an error and its ID. Otherwise, applies the update and handles modifiers.
    """
    sql = text("SELECT * FROM patch_terms(:db, :term_id, :value, :base)")

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                sql,
                {
                    "db": db_name,
                    "term_id": term_id,
                    "value": payload.val,
                    "base": payload.t,
                },
            )
            row = result.mappings().fetchone()

            if not row or row["res"] is None:
                logger.error(f"patch_terms returned empty or None for {term_id}")
                raise HTTPException(
                    status_code=400, detail="Unknown error during update"
                )

            # обработка известных ошибок через error_manager
            status_code, msg = em.get_status_and_message(row["res"]) or (None, None)
            if status_code == 400 and row["res"] == "err_term_name_exists":
                return PatchTermResponse(id=row.get("exid"), errors=msg)
            if status_code:
                em.raise_if_error(row["res"], log_context=f"PATCH /terms/{term_id}")

            # Модификаторы
            extra = payload.__pydantic_extra__ or {}
            if extra:
                vals = list(extra.keys())
                logger.info(f"Modifier rows: {vals}")
                placeholders = bindparam("placeholders", expanding=True)

                sql = text(
                    f"SELECT id, val FROM {db_name} "
                    f"WHERE val IN :placeholders AND t=0 AND up=0"
                ).bindparams(placeholders)

                mod_rows = await conn.execute(
                    sql,
                    {"placeholders": tuple(v.upper() for v in vals)},
                )

                mods = mod_rows.mappings().all()
                logger.debug(f"Found modifiers: {mods}")

                for mod in mods:
                    mid, mval = mod["id"], mod["val"]
                    await conn.execute(
                        text(f"DELETE FROM {db_name} WHERE t=:t AND up=:up"),
                        {"t": mid, "up": term_id},
                    )
                    mod_val = extra.get(mval) or extra.get(mval.lower())
                    logger.info(f"mod_val = {mod_val!r} for mval = {mval}")
                    logger.info(f"BOOLEAN_MODIFIERS: {settings.BOOLEAN_MODIFIERS}")
                    if not mod_val:
                        continue
                    if mval.upper() in settings.BOOLEAN_MODIFIERS:
                        await conn.execute(
                            text(f"INSERT INTO {db_name}(up, t) VALUES(:up, :t)"),
                            {"up": term_id, "t": mid},
                        )
                    else:
                        await conn.execute(
                            text(
                                f"INSERT INTO {db_name}(up, t, val) VALUES(:up, :t, :val)"
                            ),
                            {"up": term_id, "t": mid, "val": mod_val},
                        )

        return PatchTermResponse(id=term_id, t=payload.t, val=payload.val)

    except SQLAlchemyError as e:
        logger.exception(f"Database error while patching term {term_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.delete(
    "/{db_name}/terms/{term_id}",
    response_model=DeleteTermResponse,
)
async def delete_term(
    db_name: str = Path(..., description="Database name"),
    term_id: int = Path(..., description="ID of the term to delete"),
):
    """
    Deletes a term and all its children.

    """
    try:
        async with engine.begin() as conn:
            # === 1. Попытка удаления основного термина ===
            result = await conn.execute(
                text("SELECT delete_terms(:db, :term_id)"),
                {"db": db_name, "term_id": term_id},
            )
            res = result.scalar_one_or_none()
            if res is None or res != "1":
                status_code, message = em.get_status_and_message(res) or (None, None)
                if status_code == 200:
                    return JSONResponse(DeleteTermResponse(error=message).model_dump(exclude_none=True))
                if status_code:
                    em.raise_if_error(res, log_context=f"DELETE /terms/{term_id}")
                logger.error(f"Unexpected result from delete_terms: {res}")
                raise HTTPException(status_code=500, detail="Unexpected DB error")

            # === 2. Поиск всех вложенных терминов (обход дерева) ===
            subs = []
            queue = [term_id]
            idx = 0

            while idx < len(queue):
                parent = queue[idx]
                result = await conn.execute(
                    text(f"SELECT id FROM {db_name} WHERE up = :parent"),
                    {"parent": parent},
                )
                children = result.mappings().all()
                ids = [r["id"] for r in children]
                queue.extend(ids)
                subs.extend(ids)
                idx += 1

            # === 3. Удаление вложенных терминов ===
            if subs:
                stmt = text(f"DELETE FROM {db_name} WHERE id IN :ids").bindparams(
                    bindparam("ids", expanding=True)
                )
                await conn.execute(stmt, {"ids": subs})

            # === 4. Финальный ответ ===
            return JSONResponse(DeleteTermResponse(id=term_id, deleted_count=1 + len(subs)).model_dump(exclude_none=True))

    except SQLAlchemyError as e:
        logger.exception(f"DB error during DELETE term {term_id} in {db_name}")
        raise HTTPException(status_code=500, detail="Database error")
