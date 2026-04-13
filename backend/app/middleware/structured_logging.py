"""
Middleware for structured logging and request tracing.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.structured_logging import (
    generate_request_id,
    set_request_context,
    clear_request_context,
    get_logger
)
import time

logger = get_logger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    - Generates unique request IDs for tracing
    - Sets request context (user ID if authenticated)
    - Logs request/response information
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = generate_request_id()
        
        # Try to extract user ID from request (if authenticated)
        user_id = None
        if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            user_id = request.state.user.id
        
        # Set request context
        set_request_context(request_id, user_id)
        
        # Store request ID in request state for later use
        request.state.request_id = request_id
        
        # Track request start time
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_string=str(request.url.query),
            client_ip=request.client.host if request.client else "unknown",
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=f"{duration_ms:.2f}",
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exception
            logger.error(
                "Request failed with exception",
                method=request.method,
                path=request.url.path,
                duration_ms=f"{duration_ms:.2f}",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            
            raise
        
        finally:
            # Clear request context
            clear_request_context()
