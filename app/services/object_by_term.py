from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple, Dict, Any, List
import json

from app.db.db import engine, load_sql
from app.models.objects import TermObjectsResponse, ObjectRow, HeaderField
from app.logger import setup_logger

logger = setup_logger(__name__)


def _build_header(meta_rows):
    header_map = {}
    header = []
    for row in meta_rows:
        r = row._mapping
        logger.debug(f"Processing header row: {r}")
        if r["req_id"] not in header_map:
            field = HeaderField(
                id=r["req_id"],
                t=r["req_t"],
                name=r["req_val"],
                base=r["base"],
                ref=r["ref_id"],
                is_table_req=r["is_table_req"],
                modifiers=list(r["mods"] or []),
                original_name=r["ref_val"],
            )
            header.append(field)
            header_map[r["req_id"]] = field
    return header, header_map


def _detect_ordered_reqs(header):
    table_reqs = {f.t: f for f in header if f.is_table_req}
    ordered = {
        f.t: f
        for f in table_reqs.values()
        if any("ORDER" in mod for mod in f.modifiers)
    }
    return table_reqs, ordered


async def _fetch_metadata(conn, db_name, term_id):
    sql = text(load_sql("get_term_metadata.sql", db=db_name, term_id=term_id))
    return (await conn.execute(sql)).fetchall()


async def _fetch_objects(
    conn,
    db_name,
    term_id,
    parent_id,
    joins="",
    where_clause="",
    sql_params=None,
    limit=100,
    offset=0,
):
    sql = text(
        load_sql(
            "get_term_objects.sql",
            db=db_name,
            term_id=term_id,
            parent_id=parent_id,
            joins=joins,
            where_clauses=where_clause,
            limit=limit,
            offset=offset,
        )
    )
    return (await conn.execute(sql, sql_params or {})).fetchall()


async def _fetch_ordered_reqs(conn, obj_id, template, ordered_table_reqs):
    array_ids = ",".join(map(str, ordered_table_reqs))
    sql_text = template.replace(":obj_id", str(obj_id)).replace(":array_ids", array_ids)
    logger.debug(f"Ordered requisites SQL for object {obj_id}: {sql_text}")
    rows = (await conn.execute(text(sql_text))).fetchall()
    logger.debug(f"Ordered requisites rows for obj {obj_id}: {rows}")
    return {r[1]: r[3] for r in rows}


async def _build_reqs_map(
    conn, obj_id, reqs_template, header_map, ordered_table_reqs, ordered_req_map
):
    sql_text = reqs_template.replace(":obj_id", str(obj_id))
    reqs_rows = (await conn.execute(text(sql_text))).fetchall()

    row_data = {}
    for row in reqs_rows:
        val, req_id, field_name, alt_val = row
        field = header_map.get(req_id)
        logger.debug(f"Req row: {row}")
        if field:
            key = str(field.ref) if field.ref else field.name
            row_data[key] = val
        else:
            if any(h.t == req_id for h in header_map.values()):
                entry = row_data.setdefault(field_name, {"vals": []})
                entry["vals"].append(val)
                if req_id in ordered_table_reqs:
                    entry["q"] = ordered_req_map.get(req_id)
            elif alt_val and str(alt_val).isdigit():
                row_data[field_name] = str(alt_val)
    logger.debug(f"Built row_data: {row_data}")
    return row_data
