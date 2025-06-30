from pydantic import BaseModel
from typing import Optional


class FilterQuery(BaseModel):
    up: Optional[int] = 1
    limit: Optional[int] = 20
    offset: Optional[int] = 0

