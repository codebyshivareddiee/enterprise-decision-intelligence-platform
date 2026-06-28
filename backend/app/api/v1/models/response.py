"""Standard API Response Models."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Standardized API Response wrapper."""

    success: bool
    data: T | None = None
    message: str
    request_id: str
    timestamp: str = ""

    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {},
                "message": "Operation successful",
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2023-10-10T12:00:00Z",
            }
        }
    )


class StandardErrorResponse(BaseModel):
    """Standardized API Error Response wrapper."""

    success: bool = False
    message: str
    error_code: str
    request_id: str
    timestamp: str = ""

    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "message": "Resource not found",
                "error_code": "NOT_FOUND",
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2023-10-10T12:00:00Z",
            }
        }
    )
