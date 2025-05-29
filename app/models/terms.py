"""Pydantic models for representing term metadata and its requisites."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class TermRequisite(BaseModel):
    """Represents a single requisite (field/attribute) of a term."""

    num: Optional[int]
    id: str
    val: Optional[str]
    type: Optional[str]
    attrs: Optional[str] = None
    ref_id: Optional[str] = None
    ref: Optional[str] = None
    default_val: Optional[str] = None
    mods: Optional[List[str]] = []
    arr_id: Optional[str] = None


class TermMetadata(BaseModel):
    """Represents metadata for a term, including its requisites."""

    id: int
    up: int
    type: int
    val: str
    unique: Optional[int] = 0
    mods: Optional[List[str]] = []
    reqs: List[TermRequisite] = []


class TermCreateRequest(BaseModel):
    """Request model for creating a new term.

    Attributes:
        val: Name of the term to be created.
        t: Base type ID for the term.
        mods: All other fields passed in the request.
    """

    val: str = Field(..., description="Name of the term to create")
    t: int = Field(..., description="Base type ID of the term")
    mods: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional modifiers for the term (e.g. ALIAS, UNIQUE)",
    )

    @model_validator(mode="before")
    @classmethod
    def absorb_extra_into_mods(cls, values: dict) -> dict:
        val = values.get("val")
        t = values.get("t")

        if not val or not val.strip():
            raise ValueError("Term name (val) must not be empty")
        if not isinstance(t, int) or t <= 0:
            raise ValueError("Invalid base type (t). Must be a positive integer")

        mods = {k: v for k, v in values.items() if k not in {"val", "t"}}
        values["mods"] = mods

        return values


class TermCreateResponse(BaseModel):
    """Response model for a created term.

    Attributes:
        id: ID of the newly created (or existing) term.
        t: Base type ID of the term.
        val: Name of the term.
        warnings: Warning message if the term already existed.
    """

    id: int
    t: int
    val: str
    warnings: Optional[str] = None


class Term(BaseModel):
    """Represents a top-level term that is not referenced by any other object."""
    id: int
    val: str
    base: int  # corresponds to obj.t


class PatchTermRequest(BaseModel):
    val: str = Field(..., description="New name for the term")
    t: int = Field(..., description="New base type ID")

    class Config:
        extra = "allow"


class PatchTermResponse(BaseModel):
    id: Optional[int] = Field(None, description="ID of the updated term")
    t: Optional[int] = Field(None, description="Updated base type")
    val: Optional[str] = Field(None, description="Updated name")
    errors: Optional[str] = None
    exists: Optional[int] = None
    

class DeleteTermResponse(BaseModel):
    id: Optional[int] = Field(None, description="ID of the deleted term")
    deleted_count: Optional[int] = Field(None, description="Number of terms deleted (including children)")
    error: Optional[str] = Field(None, description="Error message, if any")