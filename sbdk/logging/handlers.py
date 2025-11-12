"""
SBDK Logging Handlers

Custom logging handlers for SBDK with file rotation, rich formatting,
and error context preservation.

Features:
    - Rotating file handler with configurable retention
    - Rich console handler for formatted output
    - Error context tracking (file, line number, function)
    - Automatic error recovery suggestions
    - Rate limiting for duplicate errors
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


class ContextAwareHandler(logging.Handler):
    """
    Handler that adds context information to log records.

    Enriches log records with:
        - File path and line number
        - Function name
        - Process and thread information
        - Error suggestions (if applicable)
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record with context information.

        Args:
            record: LogRecord to emit
        """
        # Add context attributes
        record.file_context = f"{record.pathname}:{record.lineno}"
        record.function_name = record.funcName

        # Add error code for tracking
        if record.levelno >= logging.ERROR:
            record.error_code = getattr(record, "error_code", "ERR_UNKNOWN")

        # Call parent emit (handled by subclass)
        try:
            self.handle(record)
        except Exception:
            self.handleError(record)


class RichConsoleHandler(RichHandler):
    """
    Rich-formatted console handler for SBDK.

    Extends RichHandler with SBDK-specific formatting:
        - Color-coded severity levels
        - Compact format for CLI output
        - Error context display
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        show_time: bool = True,
        show_level: bool = True,
        show_path: bool = False,
        markup: bool = True,
        rich_tracebacks: bool = True,
        tracebacks_width: int = 100,
        tracebacks_extra_lines: int = 3,
        tracebacks_theme: Optional[str] = None,
        tracebacks_word_wrap: bool = True,
        tracebacks_show_locals: bool = False,
    ) -> None:
        """
        Initialize RichConsoleHandler.

        Args:
            console: Rich Console instance
            show_time: Show timestamp
            show_level: Show log level
            show_path: Show file path (disabled by default for CLI)
            markup: Enable markup rendering
            rich_tracebacks: Enable rich traceback formatting
            tracebacks_width: Traceback display width
            tracebacks_extra_lines: Extra lines in traceback context
            tracebacks_theme: Traceback theme
            tracebacks_word_wrap: Word wrap in tracebacks
            tracebacks_show_locals: Show local variables in tracebacks
        """
        super().__init__(
            console=console,
            show_time=show_time,
            show_level=show_level,
            show_path=show_path,
            markup=markup,
            rich_tracebacks=rich_tracebacks,
            tracebacks_width=tracebacks_width,
            tracebacks_extra_lines=tracebacks_extra_lines,
            tracebacks_theme=tracebacks_theme,
            tracebacks_word_wrap=tracebacks_word_wrap,
            tracebacks_show_locals=tracebacks_show_locals,
        )
        self.console = console or Console()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to console.

        Args:
            record: LogRecord to emit
        """
        try:
            super().emit(record)
        except Exception:
            self.handleError(record)


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Rotating file handler with context information.

    Features:
        - Automatic rotation based on file size
        - Compressed backup of old logs
        - Automatic cleanup of old log files
        - Error context preservation
    """

    def __init__(
        self,
        filename: str | Path,
        max_bytes: int = 10_000_000,  # 10 MB
        backup_count: int = 10,
        encoding: str = "utf-8",
    ) -> None:
        """
        Initialize RotatingFileHandler.

        Args:
            filename: Path to log file
            max_bytes: Maximum size before rotation (default: 10 MB)
            backup_count: Number of backup files to keep
            encoding: File encoding
        """
        filename = Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            filename=str(filename),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
        )

        self.filename_path = filename

    def doRollover(self) -> None:
        """
        Perform log file rotation.

        Overrides parent to ensure directory exists and cleans old files.
        """
        self.filename_path.parent.mkdir(parents=True, exist_ok=True)
        super().doRollover()

        # Clean up very old log files
        self._cleanup_old_logs()

    def _cleanup_old_logs(self, keep_days: int = 30) -> None:
        """
        Clean up log files older than specified days.

        Args:
            keep_days: Number of days to retain logs
        """
        import time
        from pathlib import Path

        log_dir = self.filename_path.parent
        if not log_dir.exists():
            return

        now = time.time()
        max_age = keep_days * 24 * 60 * 60  # Convert days to seconds

        # Clean up rotated log files
        for log_file in log_dir.glob(f"{self.filename_path.stem}.*"):
            if log_file.suffix.endswith(("log", "txt")):
                try:
                    age = now - log_file.stat().st_mtime
                    if age > max_age:
                        log_file.unlink()
                except (OSError, AttributeError):
                    pass


class ErrorContextFilter(logging.Filter):
    """
    Filter that adds error recovery context to log records.

    Detects error types and suggests recovery actions.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter and enrich log record with error context.

        Args:
            record: LogRecord to filter

        Returns:
            True to allow the record to be logged
        """
        if record.levelno >= logging.ERROR:
            # Add error recovery context
            record.error_context = self._get_error_context(record)
            record.recovery_suggestion = self._get_recovery_suggestion(record)
        else:
            record.error_context = None
            record.recovery_suggestion = None

        return True

    @staticmethod
    def _get_error_context(record: logging.LogRecord) -> dict:
        """
        Extract error context from log record.

        Args:
            record: LogRecord to extract from

        Returns:
            Dictionary of error context
        """
        return {
            "logger": record.name,
            "level": record.levelname,
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
            "process": record.process,
            "thread": record.thread,
        }

    @staticmethod
    def _get_recovery_suggestion(record: logging.LogRecord) -> Optional[str]:
        """
        Generate recovery suggestion based on error message.

        Args:
            record: LogRecord to analyze

        Returns:
            Recovery suggestion or None
        """
        message = record.getMessage().lower()

        # Database errors
        if "database" in message or "duckdb" in message:
            if "connection" in message:
                return "Check database connection settings and ensure DuckDB is installed"
            if "corrupt" in message:
                return "Database file may be corrupted. Try backing up and recreating the database"
            if "permission" in message:
                return "Check file permissions for database directory"

        # Configuration errors
        if "config" in message:
            if "not found" in message or "missing" in message:
                return "Run 'sbdk init' to create project configuration"
            if "invalid" in message:
                return "Check sbdk_config.json syntax and values"

        # Dependency errors
        if "dependency" in message or "import" in message:
            return "Run 'uv sync' to install/update dependencies"

        # Pipeline errors
        if "pipeline" in message:
            return "Check pipeline logs with 'sbdk logs pipeline-name' and 'sbdk debug'"

        # File system errors
        if "file" in message or "path" in message:
            if "permission" in message or "permission denied" in message:
                return "Check file system permissions"
            if "no space" in message:
                return "Free up disk space and retry"

        return None


class DuplicateErrorFilter(logging.Filter):
    """
    Filter that suppresses repeated error messages.

    Tracks recently logged errors and suppresses duplicates within a time window.
    """

    def __init__(self, suppress_window_seconds: int = 60):
        """
        Initialize DuplicateErrorFilter.

        Args:
            suppress_window_seconds: Time window for duplicate suppression (default: 60s)
        """
        super().__init__()
        self.suppress_window_seconds = suppress_window_seconds
        self.last_errors: dict[str, float] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter out duplicate error messages.

        Args:
            record: LogRecord to filter

        Returns:
            True if record should be logged, False to suppress
        """
        import time

        if record.levelno < logging.ERROR:
            return True

        # Create error key from message and location
        error_key = f"{record.pathname}:{record.lineno}:{record.getMessage()}"

        now = time.time()
        last_time = self.last_errors.get(error_key, 0)

        if now - last_time < self.suppress_window_seconds:
            # Suppress duplicate
            return False

        # Update last occurrence
        self.last_errors[error_key] = now

        # Clean up old entries
        self.last_errors = {
            k: v for k, v in self.last_errors.items()
            if now - v < self.suppress_window_seconds * 10
        }

        return True
