import pytest
import sys
import os

# Добавляем путь к проекту для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Импортируем только то, что нужно для тестов
from app.models.queries import QueryColumn, QueryRequest
from app.services.query_builder import QueryBuilder


def test_query_builder_basic():
    """Тест базовой функциональности QueryBuilder"""
    # Тестовые данные из ТЗ - прямой порядок
    columns = [
        QueryColumn(
            ord=1, col_id=122, obj=64, obj_name="Пользователь",
            up=0, base=3, ref=71, req_id=107, orig_id=106
        ),
        QueryColumn(
            ord=2, col_id=126, obj=72, obj_name="Объект", 
            up=0, base=5, arr=72, req_id=111, orig_id=110, ref=75  # Объект ссылается на Доступ
        ),
        QueryColumn(
            ord=3, col_id=124, obj=71, obj_name="Роль",
            up=0, base=3, req_id=112, orig_id=None, arr=72
        ),
        QueryColumn(
            ord=4, col_id=128, obj=75, obj_name="Доступ",  # obj=75 для типа Доступа
            is_ref=True, up=0, base=75, req_id=None, orig_id=None
        ),
        QueryColumn(
            ord=5, col_id=137, obj=130, obj_name="Примечание",
            up=72, base=12, req_id=None, orig_id=None  
        )
    ]
    
    builder = QueryBuilder()
    sql = builder.build_query(columns, "ru")
    
    print(f"Generated SQL: {sql}")
    
    # Проверяем основные элементы SQL
    assert "a64.val c122" in sql  # Пользователь
    assert "a71.a71_val c124" in sql  # Роль
    assert "a72.a72_val c126" in sql  # Объект  
    assert "a75.a75_val c128" in sql  # Доступ
    assert "a130.a130_val c137" in sql  # Примечание
    assert "SELECT" in sql
    assert "FROM ru a64" in sql  # Мастер-таблица
    assert "WHERE a64.t=64 AND a64.up!=0" in sql


def test_reverse_order_query():
    """Тест обратного порядка колонок"""
    # Данные из ТЗ - обратный порядок (Доступ первый)
    columns = [
        QueryColumn(
            ord=1, col_id=128, obj=75, obj_name="Доступ",
            is_ref=True, up=0, base=75, req_id=None, orig_id=None
        ),
        QueryColumn(
            ord=2, col_id=124, obj=71, obj_name="Роль",
            up=0, base=3, req_id=112, orig_id=None, arr=72
        ),
        QueryColumn(
            ord=3, col_id=126, obj=72, obj_name="Объект", 
            up=0, base=5, req_id=111, orig_id=110, ref=75
        ),
        QueryColumn(
            ord=4, col_id=122, obj=64, obj_name="Пользователь",
            up=0, base=3, ref=71, req_id=107, orig_id=106
        ),
        QueryColumn(
            ord=5, col_id=137, obj=130, obj_name="Примечание",
            up=72, base=12, req_id=None, orig_id=None
        )
    ]
    
    builder = QueryBuilder()
    sql = builder.build_query(columns, "ru")
    
    print(f"Generated reverse SQL: {sql}")
    
    # Должен начинаться с первой колонки (Доступ)
    assert "FROM ru a75" in sql  # Мастер-таблица теперь Доступ
    assert "WHERE a75.t=75 AND a75.up!=0" in sql


def test_query_request_model():
    """Тест модели QueryRequest"""
    request = QueryRequest(
        query_id=121,
        columns=[
            QueryColumn(
                ord=1, col_id=122, obj=64, obj_name="Пользователь",
                up=0, base=3, ref=71
            )
        ],
        filters={"status": "active"},
        parameters={"limit": 100}
    )
    
    assert request.query_id == 121
    assert len(request.columns) == 1
    assert request.filters == {"status": "active"}
    assert request.parameters == {"limit": 100}


def test_query_column_model():
    """Тест модели QueryColumn"""
    column = QueryColumn(
        ord=1,
        col_id=122,
        obj=64,
        obj_name="Пользователь",
        up=0,
        base=3,
        ref=71
    )
    
    assert column.ord == 1
    assert column.col_id == 122
    assert column.obj == 64
    assert column.obj_name == "Пользователь"
    assert column.up == 0
    assert column.base == 3
    assert column.ref == 71


if __name__ == "__main__":
    pytest.main([__file__])
