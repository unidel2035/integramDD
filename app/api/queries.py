from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from typing import List
import json
import logging

from app.models.queries import QueryRequest, QueryColumn, QueryResponse
from app.services.query_builder import QueryBuilder
from app.db.db import engine, validate_table_exists, load_sql
from app.services.error_manager import error_manager as em
from app.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(tags=["queries"])

@router.get("/{db_name}/queries/{query_id}")
async def execute_query_get(
    query_id: int,
    db_name: str = Depends(validate_table_exists),
):
    """
    Выполняет запрос методом GET
    
    Args:
        query_id: ID запроса в системе
        db_name: Название базы данных
        
    Returns:
        QueryResponse: Результат выполнения запроса
        
    Raises:
        HTTPException: При ошибках выполнения запроса
    """
    try:
        logger.info(f"Executing query {query_id} on database {db_name}")
        
        # Получаем конфигурацию запроса из БД
        columns = await get_query_columns(query_id, db_name)
        
        # Строим SQL
        builder = QueryBuilder()
        sql = builder.build_query(columns, db_name)
        
        logger.info(f"Generated SQL: {sql}")
        
        # Выполняем запрос
        async with engine.begin() as conn:
            result = await conn.execute(text(sql))
            rows = result.fetchall()
            
        # Преобразуем результат в словари
        data = [dict(row._mapping) for row in rows]
        
        return JSONResponse(
            QueryResponse(
                data=data,
                columns=[col.obj_name for col in columns],
                total=len(data),
                sql=sql
            ).model_dump(exclude_none=True)
        )
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        status_code, message = em.get_status_and_message(str(e)) or (500, str(e))
        raise HTTPException(status_code=status_code, detail=message)

@router.post("/{db_name}/queries/{query_id}")
async def execute_query_post(
    query_id: int,
    request: QueryRequest,
    db_name: str = Depends(validate_table_exists),
):
    """
    Выполняет запрос методом POST с параметрами
    
    Args:
        query_id: ID запроса в системе
        request: Запрос с параметрами и фильтрами
        db_name: Название базы данных
        
    Returns:
        QueryResponse: Результат выполнения запроса
        
    Raises:
        HTTPException: При ошибках выполнения запроса
    """
    try:
        logger.info(
            f"Executing POST query {query_id} with payload: {request.model_dump(exclude_none=True)}"
        )
        
        # Строим SQL с учетом параметров
        builder = QueryBuilder()
        sql = builder.build_query(request.columns, db_name)
        
        # Применяем фильтры и параметры
        if request.filters:
            sql = apply_filters(sql, request.filters)
        
        if request.parameters:
            sql = apply_parameters(sql, request.parameters)
        
        logger.info(f"Generated SQL: {sql}")
        
        # Выполняем запрос
        async with engine.begin() as conn:
            result = await conn.execute(text(sql))
            rows = result.fetchall()
            
        # Преобразуем результат в словари
        data = [dict(row._mapping) for row in rows]
        
        return JSONResponse(
            QueryResponse(
                data=data,
                columns=[col.obj_name for col in request.columns],
                total=len(data),
                sql=sql
            ).model_dump(exclude_none=True)
        )
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        status_code, message = em.get_status_and_message(str(e)) or (500, str(e))
        raise HTTPException(status_code=status_code, detail=message)

async def get_query_columns(query_id: int, db_name: str) -> List[QueryColumn]:
    """
    Получает колонки запроса из БД
    
    Args:
        query_id: ID запроса
        db_name: Название базы данных
        
    Returns:
        List[QueryColumn]: Список колонок запроса
    """
    query = text(f"""
        SELECT DISTINCT split_part(ord.val, ':', 2)::INTEGER ord, vals.id col_id, vals.val obj
            , CASE WHEN ref_def.t!=ref_def.id THEN ref_def.val WHEN obj.up=0 THEN obj.val ELSE par.val END obj_name
            , CASE WHEN ref_def.t!=ref_def.id THEN 1 END is_ref 
            , obj.up
            , CASE obj.up WHEN 0 THEN obj.t ELSE par.t END base
            , reqs.id req_id, refs.id orig_id
            , CASE WHEN subreqs.up IS NULL THEN refs.t ELSE NULL END ref
            , subreqs.up arr
        FROM {db_name} vals LEFT JOIN {db_name} ord ON ord.up=vals.id
            LEFT JOIN {db_name} obj ON obj.id=vals.val::int8
            LEFT JOIN {db_name} par ON obj.up!=0 AND par.id=obj.t
            LEFT JOIN {db_name} ref_def ON ref_def.id=par.t
            LEFT JOIN {db_name} reqs ON obj.up=0 AND reqs.up=vals.val::int8
            LEFT JOIN {db_name} refs ON refs.id=reqs.t
            LEFT JOIN {db_name} subreqs ON subreqs.up=refs.id
        WHERE vals.t=120 AND vals.up=:query_id
            AND ((subreqs.up IS NULL AND reqs.id IS NULL) OR subreqs.up IS NOT NULL OR refs.val IS NULL)
        ORDER BY 1
    """)
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(query, {"query_id": query_id})
            rows = result.fetchall()
        
        return [QueryColumn(**dict(row._mapping)) for row in rows]
    
    except Exception as e:
        logger.error(f"Failed to get query columns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get query columns: {str(e)}")


def apply_filters(sql: str, filters: dict) -> str:
    """
    Применяет фильтры к SQL запросу
    
    Args:
        sql: Исходный SQL запрос
        filters: Словарь с фильтрами
        
    Returns:
        str: SQL запрос с примененными фильтрами
    """
    # TODO: Реализовать логику применения фильтров
    # Например, добавить WHERE условия или модифицировать существующие
    logger.info(f"Applying filters: {filters}")
    return sql


def apply_parameters(sql: str, parameters: dict) -> str:
    """
    Применяет параметры к SQL запросу
    
    Args:
        sql: Исходный SQL запрос
        parameters: Словарь с параметрами
        
    Returns:
        str: SQL запрос с примененными параметрами
    """
    # TODO: Реализовать логику применения параметров
    # Например, замена плейсхолдеров на реальные значения
    logger.info(f"Applying parameters: {parameters}")
    return sql