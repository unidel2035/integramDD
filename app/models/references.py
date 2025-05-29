from pydantic import BaseModel, Field
from typing import Optional, Dict, Union

# --------------------
# Входная модель запроса
# --------------------
class CreateReferenceRequest(BaseModel):
    id: int = Field(..., description="ID of the term to create a reference to")

# --------------------
# Модель ответа
# --------------------
class CreateReferenceResponse(BaseModel):
    id: Optional[int] = Field(None, description="ID of the created reference")
    warnings: Optional[str] = None
    errors: Optional[str] = None