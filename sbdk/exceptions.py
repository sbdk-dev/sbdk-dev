"""
SBDK Exception Hierarchy

Custom exceptions for structured error handling with actionable error messages
and appropriate exit codes for CLI operations.

Features:
    - Comprehensive exception hierarchy by category
    - Actionable error messages and recovery suggestions
    - Error context tracking (file, line, function)
    - Structured error output (dict/JSON)
    - Logging integration with automatic context capture
    - Error codes for categorization and analytics

Exit Codes:
    0: Success
    1: General user error (invalid input, configuration issues)
    2: System error (missing dependencies, IO errors)
    3: Pipeline execution error
    4: Validation error
    5: Network/API error
"""

import logging
from typing import Any, Optional


class SBDKError(Exception):
    """
    Base exception for all SBDK errors.

    All custom exceptions should inherit from this class to enable
    centralized error handling and logging.

    Attributes:
        message: Human-readable error description
        exit_code: CLI exit code (default: 1)
        error_code: Machine-readable error code for categorization
        suggestion: Actionable suggestion for fixing the error
        details: Additional context for debugging
        log_level: Logging level for this error
    """

    exit_code: int = 1
    error_code: str = "ERR_UNKNOWN"
    log_level: int = logging.ERROR

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = None,
        log_level: Optional[int] = None,
    ):
        """
        Initialize SBDK error.

        Args:
            message: Error message describing what went wrong
            suggestion: Suggested action to resolve the error
            details: Additional context dictionary for debugging
            error_code: Machine-readable error code
            log_level: Logging level (default: ERROR)
        """
        self.message = message
        self.suggestion = suggestion
        self.details = details or {}
        self.error_code = error_code or self.__class__.error_code
        self.log_level = log_level or self.__class__.log_level

        super().__init__(self.message)

        # Log the error
        self._log_error()

    def _log_error(self) -> None:
        """Log the error to the SBDK error logger."""
        try:
            logger = logging.getLogger("sbdk.errors")
            logger.log(
                self.log_level,
                f"[{self.error_code}] {self.message}",
                extra={
                    "error_code": self.error_code,
                    "suggestion": self.suggestion,
                    "details": self.details,
                },
            )
        except Exception:
            # Silently ignore logging errors
            pass

    def to_dict(self) -> dict[str, Any]:
        """
        Convert error to dictionary for structured output.

        Returns:
            Dictionary representation of the error
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "suggestion": self.suggestion,
            "exit_code": self.exit_code,
            "details": self.details
        }


# Configuration and Setup Errors (exit code: 1)

class ConfigurationError(SBDKError):
    """
    Raised when configuration is invalid or missing.

    Examples:
        - Missing sbdk_config.json file
        - Invalid JSON syntax in config
        - Required configuration fields missing
    """
    exit_code = 1
    error_code = "ERR_CONFIG_INVALID"


class ProjectNotFoundError(SBDKError):
    """
    Raised when SBDK project structure is not found.

    Examples:
        - Running commands outside SBDK project
        - Missing required project directories
    """
    exit_code = 1
    error_code = "ERR_PROJECT_NOT_FOUND"

    def __init__(self, path: str):
        super().__init__(
            message=f"Not an SBDK project: {path}",
            suggestion="Run 'sbdk init <project-name>' to create a new project, or navigate to an existing SBDK project directory",
            error_code="ERR_PROJECT_NOT_FOUND",
        )


class TemplateError(SBDKError):
    """
    Raised when project template operations fail.

    Examples:
        - Template files missing or corrupted
        - Failed to copy template structure
    """
    exit_code = 1
    error_code = "ERR_TEMPLATE_FAILED"


# System and Dependency Errors (exit code: 2)

class DependencyError(SBDKError):
    """
    Raised when required dependencies are missing or incompatible.

    Examples:
        - dbt executable not found
        - DuckDB driver unavailable
        - Python version incompatible
    """
    exit_code = 2
    error_code = "ERR_DEPENDENCY_MISSING"

    def __init__(self, dependency: str, reason: Optional[str] = None):
        message = f"Missing or incompatible dependency: {dependency}"
        if reason:
            message += f" ({reason})"

        super().__init__(
            message=message,
            suggestion=f"Install {dependency}: uv add {dependency}",
            error_code="ERR_DEPENDENCY_MISSING",
        )


class FileSystemError(SBDKError):
    """
    Raised when file system operations fail.

    Examples:
        - Permission denied
        - Disk full
        - File not found
    """
    exit_code = 2
    error_code = "ERR_FILESYSTEM"


class DatabaseError(SBDKError):
    """
    Raised when database operations fail.

    Examples:
        - DuckDB connection failed
        - SQL execution error
        - Database file corrupted
    """
    exit_code = 2
    error_code = "ERR_DATABASE"


# Pipeline Execution Errors (exit code: 3)

class PipelineError(SBDKError):
    """
    Base class for pipeline execution errors.
    """
    exit_code = 3
    error_code = "ERR_PIPELINE"


class PipelineExecutionError(PipelineError):
    """
    Raised when pipeline execution fails.

    Examples:
        - DLT pipeline crashed
        - Data generation failed
        - Pipeline timeout
    """
    error_code = "ERR_PIPELINE_EXECUTION"

    def __init__(self, pipeline_name: str, reason: str):
        super().__init__(
            message=f"Pipeline '{pipeline_name}' execution failed: {reason}",
            suggestion=f"Check pipeline logs and run 'sbdk debug' for detailed diagnostics",
            error_code="ERR_PIPELINE_EXECUTION",
        )


class DBTError(PipelineError):
    """
    Raised when dbt operations fail.

    Examples:
        - dbt compile error
        - dbt run failed
        - dbt test failures
    """
    error_code = "ERR_DBT"

    def __init__(self, command: str, exit_code: int, stderr: Optional[str] = None):
        details = {
            "command": command,
            "dbt_exit_code": exit_code,
            "stderr": stderr
        }

        super().__init__(
            message=f"dbt command failed: {command}",
            suggestion="Run 'dbt debug' to diagnose dbt configuration issues",
            details=details,
            error_code="ERR_DBT",
        )


# Validation Errors (exit code: 4)

class ValidationError(SBDKError):
    """
    Raised when input validation fails.

    Examples:
        - Invalid project name format
        - Configuration schema validation failed
        - Invalid command arguments
    """
    exit_code = 4
    error_code = "ERR_VALIDATION"


class SchemaValidationError(ValidationError):
    """
    Raised when data schema validation fails.

    Examples:
        - Pydantic model validation error
        - JSON schema validation failed
        - Required fields missing
    """
    error_code = "ERR_SCHEMA_VALIDATION"

    def __init__(self, errors: list[dict[str, Any]]):
        error_messages = [f"  - {err.get('loc', ['field'])}: {err.get('msg', 'validation failed')}" for err in errors]

        super().__init__(
            message="Configuration validation failed:\n" + "\n".join(error_messages),
            suggestion="Check your sbdk_config.json against the schema documentation",
            details={"validation_errors": errors},
            error_code="ERR_SCHEMA_VALIDATION",
        )


# Network and API Errors (exit code: 5)

class NetworkError(SBDKError):
    """
    Raised when network operations fail.

    Examples:
        - Webhook server failed to start
        - API request timeout
        - Connection refused
    """
    exit_code = 5
    error_code = "ERR_NETWORK"


class WebhookError(NetworkError):
    """
    Raised when webhook operations fail.

    Examples:
        - Failed to start webhook server
        - Webhook handler crashed
        - Invalid webhook payload
    """
    error_code = "ERR_WEBHOOK"


# Interactive UI Errors

class InteractiveError(SBDKError):
    """
    Raised when interactive UI operations fail.

    Examples:
        - Terminal not compatible
        - User cancelled operation
        - UI rendering failed
    """
    exit_code = 1
    error_code = "ERR_INTERACTIVE"


# Utility functions for error handling

def format_error_message(error: SBDKError, verbose: bool = False) -> str:
    """
    Format error message for CLI output.

    Args:
        error: SBDK exception instance
        verbose: Include detailed context and stack trace

    Returns:
        Formatted error message string
    """
    lines = [f"❌ Error: {error.message}"]

    if error.suggestion:
        lines.append(f"💡 Suggestion: {error.suggestion}")

    if verbose and error.details:
        lines.append("\nDetails:")
        for key, value in error.details.items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def exit_with_error(error: SBDKError, verbose: bool = False) -> None:
    """
    Print error message and exit with appropriate code.

    Args:
        error: SBDK exception instance
        verbose: Include detailed context
    """
    from rich.console import Console

    console = Console(stderr=True)
    console.print(f"[red]{format_error_message(error, verbose)}[/red]")

    import sys
    sys.exit(error.exit_code)
