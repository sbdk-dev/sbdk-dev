"""
SBDK Logging Module

Provides structured logging, error context tracking, and multiple output formats.

Features:
    - Rotating file handlers with automatic cleanup
    - Rich console output with formatting
    - Error context and recovery suggestions
    - Structured logging (JSON, text, compact)
    - Dedicated loggers for errors, audit, and performance
    - Automatic directory creation and management

Quick Start:
    >>> from sbdk.logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Application started")
    >>> logger.error("Something went wrong", exc_info=True)

Configuration:
    >>> from sbdk.logging.config import configure_logging
    >>> import logging
    >>> logger = configure_logging(log_level=logging.DEBUG)
"""

from sbdk.logging.config import (
    SBDKLogConfig,
    configure_logging,
    get_log_config,
    get_logger,
)
from sbdk.logging.formatters import (
    CompactFormatter,
    ContextFormatter,
    JSONFormatter,
    StructuredTextFormatter,
    create_formatter,
)
from sbdk.logging.handlers import (
    ContextAwareHandler,
    DuplicateErrorFilter,
    ErrorContextFilter,
    RichConsoleHandler,
    RotatingFileHandler,
)

__all__ = [
    # Configuration
    "SBDKLogConfig",
    "configure_logging",
    "get_log_config",
    "get_logger",
    # Handlers
    "ContextAwareHandler",
    "RichConsoleHandler",
    "RotatingFileHandler",
    "ErrorContextFilter",
    "DuplicateErrorFilter",
    # Formatters
    "JSONFormatter",
    "StructuredTextFormatter",
    "CompactFormatter",
    "ContextFormatter",
    "create_formatter",
]
