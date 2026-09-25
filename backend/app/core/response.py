from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully."
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str = "An error occurred."
    error_code: str = "INTERNAL_ERROR"
    details: Optional[Any] = None

def success_response(data: Any = None, message: str = "Success") -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
    }

def error_response(message: str = "Error", error_code: str = "ERROR", details: Any = None) -> dict:
    res = {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
    if details:
        res["details"] = details
    return res
