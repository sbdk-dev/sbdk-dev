"""
SBDK Logging Configuration

Central configuration for SBDK logging setup with file rotation,
error context, and multiple output formats.

Features:
    - Automatic log directory creation (~/.sbdk/logs/)
    - File rotation with cleanup
    - Rich console output
    - Error context and recovery suggestions
    - Structured logging formats
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from sbdk.logging.formatters import (
    CompactFormatter,
    ContextFormatter,
    JSONFormatter,
    StructuredTextFormatter,
    create_formatter,
)
from sbdk.logging.handlers import (
    DuplicateErrorFilter,
    ErrorContextFilter,
    RichConsoleHandler,
    RotatingFileHandler,
)


class SBDKLogConfig:
    """
    Central configuration for SBDK logging.

    Manages:
        - Log directory creation and maintenance
        - Handler setup and configuration
        - Filter registration
        - Logger initialization
    """

    # Default configuration
    DEFAULT_LOG_DIR = Path.home() / ".sbdk" / "logs"
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 10_000_000  # 10 MB
    DEFAULT_BACKUP_COUNT = 10

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_level: int = DEFAULT_LOG_LEVEL,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        console: Optional[Console] = None,
    ) -> None:
        """
        Initialize logging configuration.

        Args:
            log_dir: Directory for log files (default: ~/.sbdk/logs/)
            log_level: Root logger level
            max_bytes: Max size for log file rotation
            backup_count: Number of backup log files to keep
            console: Rich Console instance for output
        """
        self.log_dir = log_dir or self.DEFAULT_LOG_DIR
        self.log_level = log_level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.console = console or Console()

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Track configured loggers
        self._configured_loggers: set[str] = set()

    def get_log_file(self, name: str = "sbdk") -> Path:
        """
        Get path to log file for given name.

        Args:
            name: Log file name (without extension)

        Returns:
            Path to log file
        """
        return self.log_dir / f"{name}.log"

    def setup_root_logger(self) -> logging.Logger:
        """
        Setup and configure root logger.

        Returns:
            Configured root logger
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add console handler
        console_handler = self._create_console_handler()
        root_logger.addHandler(console_handler)

        # Add file handler
        file_handler = self._create_file_handler("sbdk")
        root_logger.addHandler(file_handler)

        # Add filters
        root_logger.addFilter(ErrorContextFilter())
        root_logger.addFilter(DuplicateErrorFilter())

        self._configured_loggers.add("root")
        return root_logger

    def setup_logger(
        self,
        name: str,
        level: Optional[int] = None,
        file_handler: bool = True,
        console_handler: bool = True,
    ) -> logging.Logger:
        """
        Setup and configure a specific logger.

        Args:
            name: Logger name
            level: Logger level (uses root level if not specified)
            file_handler: Add file handler
            console_handler: Add console handler

        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level or self.log_level)
        logger.propagate = True

        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Add handlers
        if console_handler:
            handler = self._create_console_handler()
            logger.addHandler(handler)

        if file_handler:
            handler = self._create_file_handler(name)
            logger.addHandler(handler)

        # Add filters
        logger.addFilter(ErrorContextFilter())
        logger.addFilter(DuplicateErrorFilter())

        self._configured_loggers.add(name)
        return logger

    def setup_error_logger(self) -> logging.Logger:
        """
        Setup dedicated error logger for error logs.

        Returns:
            Configured error logger
        """
        error_logger = logging.getLogger("sbdk.errors")
        error_logger.setLevel(logging.ERROR)

        # Remove existing handlers
        for handler in error_logger.handlers[:]:
            error_logger.removeHandler(handler)

        # Only log errors and above
        file_handler = RotatingFileHandler(
            self.get_log_file("errors"),
            max_bytes=self.max_bytes,
            backup_count=self.backup_count,
        )
        file_handler.setLevel(logging.ERROR)
        formatter = ContextFormatter(verbose=False)
        file_handler.setFormatter(formatter)
        error_logger.addHandler(file_handler)

        # Add filters
        error_logger.addFilter(ErrorContextFilter())

        self._configured_loggers.add("sbdk.errors")
        return error_logger

    def setup_performance_logger(self) -> logging.Logger:
        """
        Setup dedicated performance/debug logger.

        Returns:
            Configured performance logger
        """
        perf_logger = logging.getLogger("sbdk.performance")
        perf_logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        for handler in perf_logger.handlers[:]:
            perf_logger.removeHandler(handler)

        # Use compact format for performance logs
        file_handler = RotatingFileHandler(
            self.get_log_file("performance"),
            max_bytes=self.max_bytes,
            backup_count=self.backup_count,
        )
        file_handler.setFormatter(CompactFormatter())
        perf_logger.addHandler(file_handler)

        self._configured_loggers.add("sbdk.performance")
        return perf_logger

    def setup_audit_logger(self) -> logging.Logger:
        """
        Setup audit logger for tracking operations.

        Returns:
            Configured audit logger
        """
        audit_logger = logging.getLogger("sbdk.audit")
        audit_logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in audit_logger.handlers[:]:
            audit_logger.removeHandler(handler)

        # Use JSON format for audit logs
        file_handler = RotatingFileHandler(
            self.get_log_file("audit"),
            max_bytes=self.max_bytes,
            backup_count=self.backup_count,
        )
        file_handler.setFormatter(JSONFormatter())
        audit_logger.addHandler(file_handler)

        return audit_logger

    def _create_console_handler(self) -> RichConsoleHandler:
        """
        Create and configure console handler.

        Returns:
            Configured console handler
        """
        handler = RichConsoleHandler(
            console=self.console,
            show_time=True,
            show_level=True,
            show_path=False,  # Don't show file path in CLI
            rich_tracebacks=True,
            tracebacks_extra_lines=2,
        )
        handler.setLevel(self.log_level)
        handler.setFormatter(StructuredTextFormatter())
        return handler

    def _create_file_handler(self, name: str) -> RotatingFileHandler:
        """
        Create and configure file handler.

        Args:
            name: Name for log file

        Returns:
            Configured file handler
        """
        handler = RotatingFileHandler(
            self.get_log_file(name),
            max_bytes=self.max_bytes,
            backup_count=self.backup_count,
        )
        handler.setLevel(logging.DEBUG)  # Log everything to file
        handler.setFormatter(StructuredTextFormatter())
        return handler

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create logger with SBDK configuration.

        Args:
            name: Logger name

        Returns:
            Configured logger
        """
        if name not in self._configured_loggers:
            self.setup_logger(name)
        return logging.getLogger(name)

    def shutdown(self) -> None:
        """
        Shutdown logging and flush all handlers.
        """
        logging.shutdown()


# Global logging configuration instance
_log_config: Optional[SBDKLogConfig] = None


def get_log_config() -> SBDKLogConfig:
    """
    Get or create global logging configuration.

    Returns:
        Global SBDKLogConfig instance
    """
    global _log_config
    if _log_config is None:
        _log_config = SBDKLogConfig()
        _log_config.setup_root_logger()
    return _log_config


def configure_logging(
    log_level: int = logging.INFO,
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure SBDK logging system.

    Args:
        log_level: Root logger level
        log_dir: Log directory (default: ~/.sbdk/logs/)

    Returns:
        Configured root logger
    """
    config = SBDKLogConfig(log_dir=log_dir, log_level=log_level)
    globals()["_log_config"] = config
    return config.setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with SBDK configuration.

    Convenience function that uses global configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger
    """
    config = get_log_config()
    return config.get_logger(name)
