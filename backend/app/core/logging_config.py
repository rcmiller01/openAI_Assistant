"""Structured logging configuration for orchestrator."""

import os
import sys
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar(
    'request_id', default=None
)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
intent_var: ContextVar[Optional[str]] = ContextVar('intent', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context from ContextVars
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        intent = intent_var.get()
        if intent:
            log_data["intent"] = intent
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        return json.dumps(log_data)


class StructuredLogger(logging.LoggerAdapter):
    """Logger adapter that adds structured context."""
    
    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Add extra fields to log record."""
        extra = kwargs.get('extra', {})
        
        # Merge with existing extra fields
        if hasattr(self, 'extra'):
            extra.update(self.extra)
        
        kwargs['extra'] = {'extra_fields': extra}
        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatting if True, plain text if False
        log_file: Optional file path for file logging
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str, **context: Any) -> StructuredLogger:
    """
    Get a structured logger with context.
    
    Args:
        name: Logger name (usually __name__)
        **context: Additional context fields
        
    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(name)
    return StructuredLogger(logger, context)


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    intent: Optional[str] = None,
) -> None:
    """Set context variables for request tracking."""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if intent:
        intent_var.set(intent)


def clear_request_context() -> None:
    """Clear all request context variables."""
    request_id_var.set(None)
    user_id_var.set(None)
    intent_var.set(None)


# Initialize logging on import
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
LOG_FILE = os.getenv("LOG_FILE")

setup_logging(
    level=LOG_LEVEL,
    json_format=LOG_FORMAT.lower() == "json",
    log_file=LOG_FILE,
)
