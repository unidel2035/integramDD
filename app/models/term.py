from typing import Optional, List
from pydantic import BaseModel


class TermRequisite(BaseModel):
    num: Optional[int]
    id: str
    val: Optional[str]
    type: Optional[str]
    attrs: Optional[str] = None
    ref_id: Optional[str] = None
    ref: Optional[str] = None
    default_val: Optional[str] = None
    mods: Optional[List[str]] = None
    arr_id: Optional[str] = None


class TermMetadata(BaseModel):
    id: int
    up: int
    type: int
    val: str
    unique: Optional[int] = 1
    reqs: List[TermRequisite] = []
