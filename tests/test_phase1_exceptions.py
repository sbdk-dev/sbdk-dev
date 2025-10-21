"""
Unit tests for Phase 1: Exception Hierarchy
Tests all custom exceptions, error formatting, and exit codes
"""

import pytest
from sbdk.exceptions import (
    SBDKError,
    ConfigurationError,
    ProjectNotFoundError,
    TemplateError,
    DependencyError,
    FileSystemError,
    DatabaseError,
    PipelineError,
    PipelineExecutionError,
    DBTError,
    ValidationError,
    SchemaValidationError,
    NetworkError,
    WebhookError,
    InteractiveError,
    format_error_message,
)


class TestSBDKError:
    """Test base SBDKError class"""

    def test_basic_error(self):
        """Test basic error creation"""
        error = SBDKError("Test error message")
        assert str(error) == "Test error message"
        assert error.exit_code == 1
        assert error.suggestion is None
        assert error.details == {}

    def test_error_with_suggestion(self):
        """Test error with suggestion"""
        error = SBDKError(
            "Something went wrong",
            suggestion="Try running 'sbdk debug'"
        )
        assert error.message == "Something went wrong"
        assert error.suggestion == "Try running 'sbdk debug'"

    def test_error_with_details(self):
        """Test error with details"""
        error = SBDKError(
            "Error occurred",
            details={"file": "config.json", "line": 42}
        )
        assert error.details["file"] == "config.json"
        assert error.details["line"] == 42

    def test_error_to_dict(self):
        """Test error serialization to dict"""
        error = SBDKError(
            "Test error",
            suggestion="Fix it",
            details={"key": "value"}
        )
        error_dict = error.to_dict()

        assert error_dict["error_type"] == "SBDKError"
        assert error_dict["message"] == "Test error"
        assert error_dict["suggestion"] == "Fix it"
        assert error_dict["exit_code"] == 1
        assert error_dict["details"]["key"] == "value"


class TestConfigurationErrors:
    """Test configuration-related errors"""

    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("Invalid config")
        assert error.exit_code == 1
        assert "Invalid config" in str(error)

    def test_project_not_found_error(self):
        """Test ProjectNotFoundError"""
        error = ProjectNotFoundError("/path/to/project")
        assert error.exit_code == 1
        assert "/path/to/project" in error.message
        assert "sbdk init" in error.suggestion

    def test_template_error(self):
        """Test TemplateError"""
        error = TemplateError("Template missing")
        assert error.exit_code == 1


class TestSystemErrors:
    """Test system-related errors"""

    def test_dependency_error(self):
        """Test DependencyError"""
        error = DependencyError("dbt", "version mismatch")
        assert error.exit_code == 2
        assert "dbt" in error.message
        assert "version mismatch" in error.message
        assert "uv add dbt" in error.suggestion

    def test_dependency_error_without_reason(self):
        """Test DependencyError without reason"""
        error = DependencyError("duckdb")
        assert "duckdb" in error.message
        assert error.suggestion is not None

    def test_filesystem_error(self):
        """Test FileSystemError"""
        error = FileSystemError("Permission denied")
        assert error.exit_code == 2

    def test_database_error(self):
        """Test DatabaseError"""
        error = DatabaseError("Connection failed")
        assert error.exit_code == 2


class TestPipelineErrors:
    """Test pipeline execution errors"""

    def test_pipeline_error(self):
        """Test base PipelineError"""
        error = PipelineError("Pipeline failed")
        assert error.exit_code == 3

    def test_pipeline_execution_error(self):
        """Test PipelineExecutionError"""
        error = PipelineExecutionError("users", "timeout after 30s")
        assert error.exit_code == 3
        assert "users" in error.message
        assert "timeout" in error.message
        assert "sbdk debug" in error.suggestion

    def test_dbt_error(self):
        """Test DBTError"""
        error = DBTError("dbt run", 1, "Model compilation failed")
        assert error.exit_code == 3
        assert "dbt run" in error.message
        assert error.details["command"] == "dbt run"
        assert error.details["dbt_exit_code"] == 1
        assert error.details["stderr"] == "Model compilation failed"
        assert "dbt debug" in error.suggestion

    def test_dbt_error_without_stderr(self):
        """Test DBTError without stderr"""
        error = DBTError("dbt test", 2)
        assert error.details["stderr"] is None


class TestValidationErrors:
    """Test validation errors"""

    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("Invalid input")
        assert error.exit_code == 4

    def test_schema_validation_error(self):
        """Test SchemaValidationError"""
        validation_errors = [
            {"loc": ["project"], "msg": "field required"},
            {"loc": ["duckdb_path"], "msg": "field required"}
        ]
        error = SchemaValidationError(validation_errors)

        assert error.exit_code == 4
        assert "project" in error.message
        assert "duckdb_path" in error.message
        assert "field required" in error.message
        assert len(error.details["validation_errors"]) == 2


class TestNetworkErrors:
    """Test network-related errors"""

    def test_network_error(self):
        """Test NetworkError"""
        error = NetworkError("Connection timeout")
        assert error.exit_code == 5

    def test_webhook_error(self):
        """Test WebhookError"""
        error = WebhookError("Failed to start server")
        assert error.exit_code == 5


class TestInteractiveErrors:
    """Test interactive UI errors"""

    def test_interactive_error(self):
        """Test InteractiveError"""
        error = InteractiveError("Terminal not compatible")
        assert error.exit_code == 1


class TestErrorFormatting:
    """Test error formatting utilities"""

    def test_format_error_basic(self):
        """Test basic error formatting"""
        error = SBDKError("Something went wrong")
        formatted = format_error_message(error, verbose=False)

        assert "❌ Error: Something went wrong" in formatted
        assert "💡 Suggestion:" not in formatted

    def test_format_error_with_suggestion(self):
        """Test error formatting with suggestion"""
        error = SBDKError(
            "Configuration invalid",
            suggestion="Check your config file"
        )
        formatted = format_error_message(error, verbose=False)

        assert "❌ Error: Configuration invalid" in formatted
        assert "💡 Suggestion: Check your config file" in formatted

    def test_format_error_verbose(self):
        """Test verbose error formatting"""
        error = SBDKError(
            "Error occurred",
            details={"file": "test.py", "line": 42}
        )
        formatted = format_error_message(error, verbose=True)

        assert "Details:" in formatted
        assert "file: test.py" in formatted
        assert "line: 42" in formatted

    def test_format_error_not_verbose(self):
        """Test non-verbose error formatting (no details)"""
        error = SBDKError(
            "Error occurred",
            details={"file": "test.py"}
        )
        formatted = format_error_message(error, verbose=False)

        assert "Details:" not in formatted


class TestExitCodes:
    """Test exit codes are correct"""

    def test_all_exit_codes(self):
        """Test all exception classes have correct exit codes"""
        exit_code_mapping = {
            ConfigurationError: 1,
            ProjectNotFoundError: 1,
            TemplateError: 1,
            DependencyError: 2,
            FileSystemError: 2,
            DatabaseError: 2,
            PipelineError: 3,
            PipelineExecutionError: 3,
            DBTError: 3,
            ValidationError: 4,
            SchemaValidationError: 4,
            NetworkError: 5,
            WebhookError: 5,
            InteractiveError: 1,
        }

        for exception_class, expected_code in exit_code_mapping.items():
            # Create instance with appropriate args
            if exception_class == ProjectNotFoundError:
                error = exception_class("/path")
            elif exception_class == DependencyError:
                error = exception_class("dep")
            elif exception_class == PipelineExecutionError:
                error = exception_class("pipeline", "reason")
            elif exception_class == DBTError:
                error = exception_class("cmd", 1)
            elif exception_class == SchemaValidationError:
                error = exception_class([{"loc": ["field"], "msg": "error"}])
            else:
                error = exception_class("test")

            assert error.exit_code == expected_code, \
                f"{exception_class.__name__} should have exit code {expected_code}"


class TestInheritance:
    """Test exception inheritance hierarchy"""

    def test_all_inherit_from_sbdk_error(self):
        """Test all custom exceptions inherit from SBDKError"""
        exceptions = [
            ConfigurationError,
            ProjectNotFoundError,
            TemplateError,
            DependencyError,
            FileSystemError,
            DatabaseError,
            PipelineError,
            PipelineExecutionError,
            DBTError,
            ValidationError,
            SchemaValidationError,
            NetworkError,
            WebhookError,
            InteractiveError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, SBDKError), \
                f"{exc_class.__name__} should inherit from SBDKError"

    def test_specialized_inheritance(self):
        """Test specialized exception inheritance"""
        assert issubclass(PipelineExecutionError, PipelineError)
        assert issubclass(DBTError, PipelineError)
        assert issubclass(SchemaValidationError, ValidationError)
        assert issubclass(WebhookError, NetworkError)
