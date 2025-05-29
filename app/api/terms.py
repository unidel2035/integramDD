from fastapi import APIRouter, Path, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text, bindparam
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import json

from app.db.db import engine, load_sql, validate_table_exists
from app.models.terms import *
from app.services.term_builder import build_terms_from_rows
from app.auth.auth import verify_token
from app.logger import db_logger
from app.settings import settings



router = APIRouter()


@router.get(
    "/{db_name}/terms",
    response_model=List[Term],
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
    sql = load_sql("get_terms.sql", db=db_name)

    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        rows = result.mappings().all()

    return JSONResponse([dict(row) for row in rows])


@router.get(
    "/{db_name}/terms/{term_id}",
    response_model=Term,
    dependencies=[Depends(verify_token)],
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
    sql = load_sql("get_term.sql", db=db_name, term_id=term_id)

    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        rows = result.mappings().all()

    return JSONResponse([dict(row) for row in rows])


@router.get(
    "/{db_name}/metadata/{term_id}",
    response_model=TermMetadata,
    dependencies=[Depends(verify_token)],
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


@router.post(
    "/{db_name}/terms",
    response_model=TermCreateResponse,
    dependencies=[Depends(verify_token)],
)
async def create_term(
    payload: TermCreateRequest,
    db_name: str = Depends(validate_table_exists),
) -> TermCreateResponse:
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
                    "mods": json.dumps(payload.mods or {}, ensure_ascii=False),
                },
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        term_id, result_flag = row

        if result_flag == "1":
            return TermCreateResponse(id=term_id, t=payload.t, val=payload.val)

        if result_flag == "warn_term_exists":
            return TermCreateResponse(
                id=term_id, t=payload.t, val=payload.val, warnings="Term already exists"
            )

        db_logger.exception(f"Unexpected result from post_terms: {result_flag}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except SQLAlchemyError as _e:
        db_logger.exception(f"Database error while executing post_terms: {_e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch(
    "/{db_name}/terms/{term_id}",
    response_model=PatchTermResponse,
    dependencies=[Depends(verify_token)],
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

    async with engine.begin() as conn:  # type: AsyncConnection
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
        print(row)

        if not row or row["res"] is None:
            return JSONResponse(
                status_code=400, content={"errors": "Unknown error during update."}
            )

        if row["res"] == "err_term_name_exists":
            return JSONResponse(
                PatchTermResponse(id=row["exid"], errors=row["res"]).model_dump(
                    exclude_none=True
                )
            )

        # Обработка модификаторов
        if payload.__pydantic_extra__:
            vals = list(payload.__pydantic_extra__.keys())
            placeholders = ",".join([f"'{v.upper()}'" for v in vals])
            print(f"Placeholders: {placeholders}")
            mod_query = (
                f"SELECT id, val FROM {db_name} "
                f"WHERE val IN ({placeholders}) AND t=0 AND up=0"
            )
            mod_rows = await conn.execute(text(mod_query))
            mods = mod_rows.mappings().all()
            print(f"Modifiers found: {mods}")
            for mod in mods:
                mid, mval = mod["id"], mod["val"]
                await conn.execute(
                    text(f"DELETE FROM {db_name} WHERE t=:t AND up=:up"),
                    {"t": mid, "up": term_id},
                )
                mod_val = payload.__pydantic_extra__.get(mval.lower(), None)
                print(f"Modifier value for {mval}: {mod_val}")
                if mod_val is None or mod_val == "":
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

    return JSONResponse(
        PatchTermResponse(id=term_id, t=payload.t, val=payload.val).model_dump(
            exclude_none=True
        )
    )

@router.delete(
    "/{db_name}/terms/{term_id}",
    response_model=DeleteTermResponse,
    dependencies=[Depends(verify_token)],
)
async def delete_term(
    db_name: str = Path(..., description="Database name"),
    term_id: int = Path(..., description="ID of the term to delete"),
):
    """
    Deletes a term and all its children (via `up = term_id`).
    Step 1: calls delete_terms(...) to check and delete base term.
    Step 2: collects children recursively and deletes them in Python.
    """
    async with engine.begin() as conn:  # type: AsyncConnection

        #1
        sql = text("SELECT delete_terms(:db, :term_id)")
        result = await conn.execute(sql, {"db": db_name, "term_id": term_id})
        res = result.scalar_one_or_none()

        if res == "err_term_not_found":
            raise HTTPException(status_code=404, detail="Term not found")

        if res == "err_term_is_in_use":
            return JSONResponse(
                DeleteTermResponse(error="There are objects of this type").model_dump(exclude_none=True)
            )

        if res is None or res != "1":
            return JSONResponse(
                DeleteTermResponse(error="Unknown error during deletion").model_dump(exclude_none=True)
            )

        #2
        subs = []
        queue = [term_id]
        idx = 0

        while idx < len(queue):
            parent = queue[idx]
            sql = text(f"SELECT id FROM {db_name} WHERE up = :parent")
            result = await conn.execute(sql, {"parent": parent})
            children = result.mappings().all()
            ids = [r["id"] for r in children]
            queue.extend(ids)
            subs.extend(ids)
            idx += 1

        #3
        if subs:
            stmt = text(f"DELETE FROM {db_name} WHERE id IN :ids").bindparams(
                bindparam("ids", expanding=True)
            )
            await conn.execute(stmt, {"ids": subs})

        return JSONResponse(
            DeleteTermResponse(id=term_id, deleted_count=1 + len(subs)).model_dump(exclude_none=True)
        )