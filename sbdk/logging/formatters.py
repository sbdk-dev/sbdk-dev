"""
SBDK Logging Formatters

Custom log formatters for SBDK with structured output formats.

Features:
    - JSON formatted logs for machine parsing
    - Structured text format for human readability
    - Error context formatting
    - Stack trace formatting
"""

import json
import logging
import traceback
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON records.

    Each log entry is a complete JSON object with metadata.
    """

    def __init__(
        self,
        include_context: bool = True,
        include_traceback: bool = True,
        include_timestamp: bool = True,
    ) -> None:
        """
        Initialize JSONFormatter.

        Args:
            include_context: Include error context in output
            include_traceback: Include traceback for exceptions
            include_timestamp: Include timestamp in output
        """
        super().__init__()
        self.include_context = include_context
        self.include_traceback = include_traceback
        self.include_timestamp = include_timestamp

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: LogRecord to format

        Returns:
            JSON-formatted log string
        """
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add timestamp
        if self.include_timestamp:
            log_data["timestamp"] = self.formatTime(record)

        # Add error context
        if self.include_context and record.levelno >= logging.ERROR:
            log_data["context"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
                "process": record.process,
                "thread": record.thread,
            }

            # Add error recovery suggestion if available
            if hasattr(record, "recovery_suggestion") and record.recovery_suggestion:
                log_data["suggestion"] = record.recovery_suggestion

            if hasattr(record, "error_context") and record.error_context:
                log_data["error_details"] = record.error_context

        # Add traceback for exceptions
        if self.include_traceback and record.exc_info:
            log_data["traceback"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data["extra"] = record.extra_fields

        return json.dumps(log_data, default=str)


class StructuredTextFormatter(logging.Formatter):
    """
    Formatter for human-readable structured text output.

    Produces nicely formatted multi-line logs with clear hierarchy.
    """

    def __init__(
        self,
        include_context: bool = True,
        include_traceback: bool = True,
        time_format: str = "%Y-%m-%d %H:%M:%S",
        line_sep: str = "  ",
    ) -> None:
        """
        Initialize StructuredTextFormatter.

        Args:
            include_context: Include error context
            include_traceback: Include traceback for exceptions
            time_format: Format string for timestamps
            line_sep: Prefix for continuation lines
        """
        super().__init__(datefmt=time_format)
        self.include_context = include_context
        self.include_traceback = include_traceback
        self.line_sep = line_sep

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured text.

        Args:
            record: LogRecord to format

        Returns:
            Structured text log string
        """
        lines = []

        # Format timestamp and level
        timestamp = self.formatTime(record)
        level = record.levelname
        logger = record.name

        # Main log line
        message = record.getMessage()
        lines.append(f"[{timestamp}] {level:8} [{logger}] {message}")

        # Add context for errors
        if self.include_context and record.levelno >= logging.ERROR:
            lines.append(f"{self.line_sep}→ File: {record.pathname}:{record.lineno}")
            lines.append(f"{self.line_sep}→ Function: {record.funcName}")

            # Add recovery suggestion
            if hasattr(record, "recovery_suggestion") and record.recovery_suggestion:
                lines.append(f"{self.line_sep}⚡ Suggestion: {record.recovery_suggestion}")

        # Add traceback for exceptions
        if self.include_traceback and record.exc_info:
            exc_text = self.formatException(record.exc_info)
            exc_lines = exc_text.split("\n")
            for exc_line in exc_lines:
                if exc_line:
                    lines.append(f"{self.line_sep}{exc_line}")

        return "\n".join(lines)


class CompactFormatter(logging.Formatter):
    """
    Formatter for compact single-line log output.

    Useful for log aggregation and minimal terminal output.
    """

    def __init__(
        self,
        time_format: str = "%H:%M:%S",
        show_logger: bool = True,
    ) -> None:
        """
        Initialize CompactFormatter.

        Args:
            time_format: Format string for timestamps
            show_logger: Include logger name in output
        """
        super().__init__(datefmt=time_format)
        self.show_logger = show_logger

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record in compact form.

        Args:
            record: LogRecord to format

        Returns:
            Compact single-line log string
        """
        timestamp = self.formatTime(record)
        level = record.levelname[0]  # Just first letter (E, W, I, D)

        if self.show_logger:
            return f"{timestamp} {level} {record.name}: {record.getMessage()}"
        else:
            return f"{timestamp} {level} {record.getMessage()}"


class ContextFormatter(logging.Formatter):
    """
    Formatter that emphasizes error context and recovery suggestions.

    Designed for error log files and debugging.
    """

    def __init__(
        self,
        time_format: str = "%Y-%m-%d %H:%M:%S",
        verbose: bool = False,
    ) -> None:
        """
        Initialize ContextFormatter.

        Args:
            time_format: Format string for timestamps
            verbose: Include all available context
        """
        super().__init__(datefmt=time_format)
        self.verbose = verbose

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with emphasis on context.

        Args:
            record: LogRecord to format

        Returns:
            Context-focused log string
        """
        lines = []

        # Header with timestamp and level
        timestamp = self.formatTime(record)
        lines.append(f"\n{'='*70}")
        lines.append(f"[{timestamp}] {record.levelname}")
        lines.append(f"{'='*70}")

        # Message
        message = record.getMessage()
        lines.append(f"Message: {message}")

        # Location
        lines.append(
            f"Location: {record.pathname}:{record.lineno} in {record.funcName}()"
        )

        # Context information
        if hasattr(record, "error_context") and record.error_context:
            lines.append("\nContext:")
            for key, value in record.error_context.items():
                lines.append(f"  {key:12} : {value}")

        # Recovery suggestion
        if hasattr(record, "recovery_suggestion") and record.recovery_suggestion:
            lines.append(f"\nRecovery Suggestion: {record.recovery_suggestion}")

        # Exception details
        if record.exc_info:
            lines.append("\nException Details:")
            exc_text = self.formatException(record.exc_info)
            for exc_line in exc_text.split("\n"):
                if exc_line:
                    lines.append(f"  {exc_line}")

        # Verbose extras
        if self.verbose:
            lines.append(f"\nAdditional Context:")
            lines.append(f"  Logger      : {record.name}")
            lines.append(f"  Module      : {record.module}")
            lines.append(f"  Process ID  : {record.process}")
            lines.append(f"  Thread ID   : {record.thread}")
            lines.append(f"  Thread Name : {record.threadName}")

        return "\n".join(lines)


def create_formatter(
    format_type: str = "structured",
    verbose: bool = False,
    time_format: Optional[str] = None,
) -> logging.Formatter:
    """
    Factory function to create a formatter.

    Args:
        format_type: Type of formatter (json, structured, compact, context)
        verbose: Enable verbose output
        time_format: Custom time format string

    Returns:
        Configured logging formatter
    """
    if format_type == "json":
        return JSONFormatter(
            include_context=True,
            include_traceback=True,
            include_timestamp=True,
        )
    elif format_type == "structured":
        return StructuredTextFormatter(
            include_context=True,
            include_traceback=True,
            time_format=time_format or "%Y-%m-%d %H:%M:%S",
        )
    elif format_type == "compact":
        return CompactFormatter(
            time_format=time_format or "%H:%M:%S",
            show_logger=True,
        )
    elif format_type == "context":
        return ContextFormatter(
            time_format=time_format or "%Y-%m-%d %H:%M:%S",
            verbose=verbose,
        )
    else:
        # Default to structured
        return StructuredTextFormatter()
