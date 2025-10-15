from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class JoinType(str, Enum):
    REFERENCE = "reference"  # ссылка
    DEPENDENT = "dependent"  # подчиненная таблица

class QueryColumn(BaseModel):
    col_id: int
    obj: int
    obj_name: str
    is_ref: Optional[bool] = None
    up: int
    base: int
    req_id: Optional[int] = None
    orig_id: Optional[int] = None
    ref: Optional[int] = None
    arr: Optional[int] = None
    ord: int

class QueryRequest(BaseModel):
    columns: List[QueryColumn]
    filters: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    data: List[Dict[str, Any]]
    columns: List[str]
    total: int
    sql: Optional[str] = None
    warning: Optional[str] = None

class JoinInfo(BaseModel):
    table_alias: str
    join_type: JoinType
    parent_alias: str
    condition: str
    subquery: Optional[str] = None