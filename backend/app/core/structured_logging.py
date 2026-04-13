"""
Structured logging for the application.

Provides JSON-formatted logging with context, tracing, and structured fields
for easy parsing and analysis in production environments.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from contextvars import ContextVar

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
session_id_var: ContextVar[str] = ContextVar("session_id", default="")


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context variables if available
        if request_id := request_id_var.get():
            log_data["request_id"] = request_id
        if user_id := user_id_var.get():
            log_data["user_id"] = user_id
        if session_id := session_id_var.get():
            log_data["session_id"] = session_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "message": str(record.exc_info[1]),
            }
        
        # Add extra fields from record if present
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra
        
        # Add custom fields if attached to record
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName", 
                          "levelname", "levelno", "lineno", "module", "msecs", "message",
                          "pathname", "process", "processName", "relativeCreated", "thread",
                          "threadName", "exc_info", "exc_text", "stack_info", "getMessage",
                          "extra"]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class StructuredLogger(logging.Logger):
    """Logger with structured logging support."""
    
    def with_context(self, **context) -> "StructuredLogger":
        """Add context to logging calls."""
        self._context = context
        return self
    
    def _log_with_extra(self, level: int, msg: str, args, exc_info=None, extra=None, stack_info=None, **kwargs):
        """Log with extra context."""
        if extra is None:
            extra = {}
        
        # Merge context if set
        if hasattr(self, "_context"):
            extra.update(self._context)
            delattr(self, "_context")
        
        # Add any additional kwargs as extra fields
        extra.update(kwargs)
        
        super()._log(level, msg, args, exc_info, extra, stack_info)
    
    def info(self, msg: str, **kwargs):
        """Log info message with extra fields."""
        self._log_with_extra(logging.INFO, msg, (), extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message with extra fields."""
        self._log_with_extra(logging.WARNING, msg, (), extra=kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log error message with extra fields."""
        self._log_with_extra(logging.ERROR, msg, (), extra=kwargs)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message with extra fields."""
        self._log_with_extra(logging.DEBUG, msg, (), extra=kwargs)
    
    def critical(self, msg: str, **kwargs):
        """Log critical message with extra fields."""
        self._log_with_extra(logging.CRITICAL, msg, (), extra=kwargs)


# Set custom logger class
logging.setLoggerClass(StructuredLogger)


def setup_logging(level: str = "INFO") -> None:
    """Set up structured logging for the application."""
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Add new handler
    root_logger.addHandler(console_handler)
    
    # Set loggers for noisy libraries
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return logging.getLogger(name)


def set_request_context(request_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
    """Set request context for tracing."""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if session_id:
        session_id_var.set(session_id)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_var.set("")
    user_id_var.set("")
    session_id_var.set("")


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())
