"""
Standardized error handling and response formatting for FastAPI.
All API responses follow consistent structure.
"""
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Standard API exception for consistent error responses."""
    
    def __init__(
        self,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        message: str = "An error occurred",
        details: dict = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


def format_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict = None,
    path: str = "/",
):
    """Format standard error response."""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
        },
        "timestamp": datetime.utcnow().isoformat(),
        "path": path,
    }


def format_success_response(data, path: str = "/"):
    """Format standard success response."""
    return {
        "success": True,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "path": path,
    }


async def api_exception_handler(request: Request, exc: APIException):
    """Handle APIException with standardized response."""
    logger.error(f"API Error: {exc.error_code} - {exc.message}", extra={
        "status_code": exc.status_code,
        "error_code": exc.error_code,
        "path": str(request.url.path),
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=str(request.url.path),
        ),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standardized response."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(f"Validation Error: {len(errors)} field(s)", extra={
        "errors": errors,
        "path": str(request.url.path),
    })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": errors},
            path=str(request.url.path),
        ),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with standardized response."""
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}", extra={
        "exception_type": type(exc).__name__,
        "path": str(request.url.path),
    }, exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={},
            path=str(request.url.path),
        ),
    )
