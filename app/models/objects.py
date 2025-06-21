from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Dict, Any, Optional, List, Union


class ObjectCreateRequest(BaseModel):
    """
    Request model for creating a new object via the /object endpoint.

    Attributes:
        id (int): Type ID of the object (term ID).
        up (int): Parent object ID. For root-level objects, this should be 1.
        attrs (Dict[str, Any]): Dictionary of object attributes. Must include 't{id}' (e.g., 't32').
                                Keys may also use term names instead of t-codes.

    Validation:
        Ensures that the key 't{id}' exists in attrs and has a non-empty value,
        since it represents the object's main value and is required by the post_objects() SQL procedure.
    """

    id: int = Field(..., description="Type ID of the object to create")
    up: int = Field(..., description="Parent object ID (1 for root)")
    attrs: Dict[str, Any] = Field(..., description="Attributes of the object including 't{id}' or term names")

    @model_validator(mode="after")
    def validate_attrs(self) -> "ObjectCreateRequest":
        """
        Validates that:
        - `attrs` contains a key of the form 't{id}' where `id` is the object type.
        - This key has a non-empty value (e.g., not '', None, or whitespace-only string).

        Returns:
            ObjectCreateRequest: The validated object.

        Raises:
            ValueError: If 't{id}' is missing or has an empty value.
        """
        object_key = f"t{self.id}"

        if object_key not in self.attrs:
            raise ValueError(f"Missing required key '{object_key}' in 'attrs'")

        value = self.attrs[object_key]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"Empty value for required attribute '{object_key}' in 'attrs'")

        return self


class ObjectCreateResponse(BaseModel):
    """
    Response model for successful object creation via the /object endpoint.

    Attributes:
        id (int): ID of the created object.
        up (int): ID of the parent object.
        t (int): Type ID (term) of the created object.
        val (str): The main value assigned to the object (e.g., its name or label).
        warning (Optional[str]): Optional warning message (e.g., if object already existed).
    """

    id: int
    up: int
    t: int
    val: str
    warning: Optional[str] = None


class PatchObjectRequest(BaseModel):
    """
    Arbitrary JSON map of attributes, where keys are of the form 't{id}' and values are strings.
    Example: {"t101": "value", "t102": "another"}
    """
    model_config = ConfigDict(extra="allow")
    
    def get_payload(self) -> Dict[str, Any]:
        return self.__pydantic_extra__ if hasattr(self, '__pydantic_extra__') and self.__pydantic_extra__ else {}


class PatchObjectResponse(BaseModel):
    id: int
    val: Optional[str] = None
    error: Optional[str] = None
    warnings: Optional[str] = None
    

class DeleteObjectResponse(BaseModel):
    id: int = Field(..., description="ID of the deleted object")
    
class HeaderField(BaseModel):
    id: int
    t: int
    name: str
    base: int
    ref: Optional[int] = None
    modifiers: List[str] = []
    original_name: Optional[str] = None
    array: Optional[int] = None

class ObjectRow(BaseModel):
    id: int
    up: int
    val: str
    reqs: Dict[str, str] = {}

class TermObjectsResponse(BaseModel):
    t: int
    name: str
    base: int
    header: List[HeaderField]
    objects: List[ObjectRow]