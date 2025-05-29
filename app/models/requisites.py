from pydantic import BaseModel, Field
from typing import Optional, Dict, Union

class RequisiteModifiers(BaseModel):
    unique: Optional[int] = Field(None, description="1 if field must be unique")
    notnull: Optional[int] = Field(None, description="1 if field must be not null")
    alias: Optional[str] = Field(None, description="Field alias")

class AddRequisitePayload(BaseModel):
    t: int = Field(..., description="Type ID of the requisite to add")

    class Config:
        extra = "allow"

class AddRequisiteResponse(BaseModel):
    id: int
    warnings: Optional[str] = None