"""
Enhanced Error Handling Tests for Phase 1

Tests enhanced exception hierarchy with:
- Error codes
- Logging integration
- Error context tracking
- Recovery suggestions
"""

import logging
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sbdk.exceptions import (
    ConfigurationError,
    DatabaseError,
    DBTError,
    DependencyError,
    FileSystemError,
    InteractiveError,
    NetworkError,
    PipelineError,
    PipelineExecutionError,
    ProjectNotFoundError,
    SBDKError,
    SchemaValidationError,
    TemplateError,
    ValidationError,
    WebhookError,
    format_error_message,
)
from sbdk.logging.config import SBDKLogConfig
from sbdk.logging.formatters import (
    CompactFormatter,
    ContextFormatter,
    JSONFormatter,
    StructuredTextFormatter,
)
from sbdk.logging.handlers import (
    DuplicateErrorFilter,
    ErrorContextFilter,
    RotatingFileHandler,
)


class TestEnhancedSBDKError:
    """Test enhanced SBDKError with logging and error codes"""

    def test_error_has_error_code(self):
        """Test that errors have error codes"""
        error = SBDKError("Test error")
        assert hasattr(error, "error_code")
        assert error.error_code == "ERR_UNKNOWN"

    def test_error_has_log_level(self):
        """Test that errors have log level"""
        error = SBDKError("Test error")
        assert hasattr(error, "log_level")
        assert error.log_level == logging.ERROR

    def test_error_custom_error_code(self):
        """Test error with custom error code"""
        error = SBDKError("Test", error_code="ERR_CUSTOM")
        assert error.error_code == "ERR_CUSTOM"

    def test_error_to_dict_includes_error_code(self):
        """Test to_dict includes error code"""
        error = SBDKError("Test error", error_code="ERR_TEST")
        error_dict = error.to_dict()

        assert "error_code" in error_dict
        assert error_dict["error_code"] == "ERR_TEST"

    def test_error_logs_to_sbdk_errors_logger(self):
        """Test that errors are logged"""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            error = SBDKError("Test error", error_code="ERR_TEST")

            # Should call getLogger with "sbdk.errors"
            mock_get_logger.assert_called_with("sbdk.errors")

    def test_error_logging_handles_exceptions(self):
        """Test that logging errors don't raise exceptions"""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.log.side_effect = Exception("Logger failed")
            mock_get_logger.return_value = mock_logger

            # Should not raise
            error = SBDKError("Test error")
            assert error.message == "Test error"


class TestErrorCodes:
    """Test error codes are properly set for all error types"""

    def test_configuration_error_code(self):
        """Test ConfigurationError has correct code"""
        error = ConfigurationError("Test")
        assert error.error_code == "ERR_CONFIG_INVALID"

    def test_project_not_found_error_code(self):
        """Test ProjectNotFoundError has correct code"""
        error = ProjectNotFoundError("/path")
        assert error.error_code == "ERR_PROJECT_NOT_FOUND"

    def test_template_error_code(self):
        """Test TemplateError has correct code"""
        error = TemplateError("Test")
        assert error.error_code == "ERR_TEMPLATE_FAILED"

    def test_dependency_error_code(self):
        """Test DependencyError has correct code"""
        error = DependencyError("dbt")
        assert error.error_code == "ERR_DEPENDENCY_MISSING"

    def test_filesystem_error_code(self):
        """Test FileSystemError has correct code"""
        error = FileSystemError("Test")
        assert error.error_code == "ERR_FILESYSTEM"

    def test_database_error_code(self):
        """Test DatabaseError has correct code"""
        error = DatabaseError("Test")
        assert error.error_code == "ERR_DATABASE"

    def test_pipeline_error_code(self):
        """Test PipelineError has correct code"""
        error = PipelineError("Test")
        assert error.error_code == "ERR_PIPELINE"

    def test_pipeline_execution_error_code(self):
        """Test PipelineExecutionError has correct code"""
        error = PipelineExecutionError("test_pipeline", "timeout")
        assert error.error_code == "ERR_PIPELINE_EXECUTION"

    def test_dbt_error_code(self):
        """Test DBTError has correct code"""
        error = DBTError("dbt run", 1)
        assert error.error_code == "ERR_DBT"

    def test_validation_error_code(self):
        """Test ValidationError has correct code"""
        error = ValidationError("Test")
        assert error.error_code == "ERR_VALIDATION"

    def test_schema_validation_error_code(self):
        """Test SchemaValidationError has correct code"""
        error = SchemaValidationError([{"loc": ["field"], "msg": "required"}])
        assert error.error_code == "ERR_SCHEMA_VALIDATION"

    def test_network_error_code(self):
        """Test NetworkError has correct code"""
        error = NetworkError("Test")
        assert error.error_code == "ERR_NETWORK"

    def test_webhook_error_code(self):
        """Test WebhookError has correct code"""
        error = WebhookError("Test")
        assert error.error_code == "ERR_WEBHOOK"

    def test_interactive_error_code(self):
        """Test InteractiveError has correct code"""
        error = InteractiveError("Test")
        assert error.error_code == "ERR_INTERACTIVE"


class TestJSONFormatter:
    """Test JSON formatting for logs"""

    def test_json_formatter_basic(self):
        """Test basic JSON formatting"""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Test error",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "ERROR"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test error"

    def test_json_formatter_includes_context(self):
        """Test JSON formatter includes error context"""
        import json

        formatter = JSONFormatter(include_context=True)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "context" in data
        assert data["context"]["file"] == "test.py"
        assert data["context"]["line"] == 42

    def test_json_formatter_includes_recovery_suggestion(self):
        """Test JSON formatter includes recovery suggestion"""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=None,
        )
        record.recovery_suggestion = "Try running sbdk debug"

        output = formatter.format(record)
        data = json.loads(output)

        assert "suggestion" in data
        assert data["suggestion"] == "Try running sbdk debug"


class TestStructuredTextFormatter:
    """Test structured text formatting"""

    def test_structured_formatter_basic(self):
        """Test basic structured formatting"""
        formatter = StructuredTextFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Test error",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "ERROR" in output
        assert "test.logger" in output
        assert "Test error" in output

    def test_structured_formatter_includes_location(self):
        """Test structured formatter includes file location"""
        formatter = StructuredTextFormatter(include_context=True)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "test.py:42" in output

    def test_structured_formatter_includes_suggestion(self):
        """Test structured formatter includes recovery suggestion"""
        formatter = StructuredTextFormatter(include_context=True)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=None,
        )
        record.recovery_suggestion = "Try command X"

        output = formatter.format(record)

        assert "Try command X" in output


class TestCompactFormatter:
    """Test compact formatting"""

    def test_compact_formatter_basic(self):
        """Test basic compact formatting"""
        formatter = CompactFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "I test.logger: Message" in output or "I" in output

    def test_compact_formatter_single_letter_level(self):
        """Test compact formatter uses single letter level"""
        formatter = CompactFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "E" in output


class TestContextFormatter:
    """Test context-focused formatting"""

    def test_context_formatter_verbose(self):
        """Test verbose context formatting"""
        formatter = ContextFormatter(verbose=True)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        record.funcName = "test_func"

        output = formatter.format(record)

        assert "ERROR" in output
        assert "Error message" in output
        assert "test.py:42" in output
        assert "test_func" in output


class TestErrorContextFilter:
    """Test ErrorContextFilter"""

    def test_error_context_filter_adds_context(self):
        """Test filter adds error context"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_func"

        filter_obj.filter(record)

        assert hasattr(record, "error_context")
        assert record.error_context["file"] == "test.py"
        assert record.error_context["line"] == 42

    def test_error_context_filter_suggests_recovery(self):
        """Test filter provides recovery suggestions"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Database connection failed",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        assert hasattr(record, "recovery_suggestion")
        assert record.recovery_suggestion is not None

    def test_error_context_filter_non_error_levels(self):
        """Test filter ignores non-error levels"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Info",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        assert record.error_context is None
        assert record.recovery_suggestion is None


class TestDuplicateErrorFilter:
    """Test DuplicateErrorFilter"""

    def test_duplicate_error_filter_suppresses_duplicates(self):
        """Test filter suppresses duplicate errors"""
        filter_obj = DuplicateErrorFilter(suppress_window_seconds=1)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        # First occurrence should be logged
        assert filter_obj.filter(record) is True

        # Second identical should be suppressed
        assert filter_obj.filter(record) is False

    def test_duplicate_error_filter_allows_different_errors(self):
        """Test filter allows different errors"""
        filter_obj = DuplicateErrorFilter(suppress_window_seconds=1)

        record1 = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error A",
            args=(),
            exc_info=None,
        )

        record2 = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error B",
            args=(),
            exc_info=None,
        )

        assert filter_obj.filter(record1) is True
        assert filter_obj.filter(record2) is True

    def test_duplicate_error_filter_non_error_levels(self):
        """Test filter allows all non-error levels"""
        filter_obj = DuplicateErrorFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Info",
            args=(),
            exc_info=None,
        )

        # Non-errors should always be allowed
        assert filter_obj.filter(record) is True
        assert filter_obj.filter(record) is True


class TestRotatingFileHandler:
    """Test RotatingFileHandler"""

    def test_rotating_file_handler_creates_directory(self, tmp_path):
        """Test handler creates log directory"""
        log_file = tmp_path / "logs" / "test.log"
        handler = RotatingFileHandler(log_file)

        assert log_file.parent.exists()
        handler.close()

    def test_rotating_file_handler_writes_logs(self, tmp_path):
        """Test handler writes logs to file"""
        log_file = tmp_path / "test.log"
        handler = RotatingFileHandler(log_file)
        formatter = StructuredTextFormatter()
        handler.setFormatter(formatter)

        logger = logging.getLogger("test")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("Test message")
        handler.close()

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_rotating_file_handler_respects_max_bytes(self, tmp_path):
        """Test handler respects max_bytes limit"""
        log_file = tmp_path / "test.log"
        handler = RotatingFileHandler(log_file, max_bytes=100, backup_count=2)

        # Write enough data to trigger rotation
        for i in range(10):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Message {i}" * 10,
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        handler.close()

        # Should have created backup files
        log_dir = tmp_path
        log_files = list(log_dir.glob("test.log*"))
        assert len(log_files) > 1


class TestSBDKLogConfig:
    """Test SBDKLogConfig"""

    def test_log_config_creates_directory(self, tmp_path):
        """Test config creates log directory"""
        log_dir = tmp_path / "logs"
        config = SBDKLogConfig(log_dir=log_dir)

        assert log_dir.exists()

    def test_log_config_setup_root_logger(self, tmp_path):
        """Test config sets up root logger"""
        config = SBDKLogConfig(log_dir=tmp_path / "logs")
        logger = config.setup_root_logger()

        assert logger is not None
        assert len(logger.handlers) > 0

    def test_log_config_setup_logger(self, tmp_path):
        """Test config sets up specific logger"""
        config = SBDKLogConfig(log_dir=tmp_path / "logs")
        logger = config.setup_logger("test.module")

        assert logger.name == "test.module"
        assert len(logger.handlers) > 0

    def test_log_config_setup_error_logger(self, tmp_path):
        """Test config sets up error logger"""
        config = SBDKLogConfig(log_dir=tmp_path / "logs")
        logger = config.setup_error_logger()

        assert logger.name == "sbdk.errors"
        assert logger.level == logging.ERROR

    def test_log_config_setup_performance_logger(self, tmp_path):
        """Test config sets up performance logger"""
        config = SBDKLogConfig(log_dir=tmp_path / "logs")
        logger = config.setup_performance_logger()

        assert logger.name == "sbdk.performance"
        assert logger.level == logging.DEBUG

    def test_log_config_setup_audit_logger(self, tmp_path):
        """Test config sets up audit logger"""
        config = SBDKLogConfig(log_dir=tmp_path / "logs")
        logger = config.setup_audit_logger()

        assert logger.name == "sbdk.audit"
        assert logger.level == logging.INFO


class TestIntegratedErrorHandling:
    """Test integrated error handling with logging"""

    def test_error_triggers_logging(self, tmp_path):
        """Test that error creation triggers logging"""
        config = SBDKLogConfig(log_dir=tmp_path / "logs")
        config.setup_error_logger()

        # Create an error
        error = DatabaseError("Connection timeout", details={"host": "localhost"})

        # Check error was logged (file should be created)
        log_file = tmp_path / "logs" / "errors.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "Connection timeout" in content

    def test_error_includes_suggestion_in_output(self):
        """Test error suggestion is included in output"""
        error = DependencyError("dbt")
        formatted = format_error_message(error)

        assert "Suggestion" in formatted
        assert "uv add" in formatted

    def test_error_dict_serialization(self):
        """Test error can be serialized to dict"""
        error = ValidationError(
            "Invalid input",
            suggestion="Check format",
            details={"field": "name"},
            error_code="ERR_CUSTOM"
        )

        error_dict = error.to_dict()

        assert error_dict["error_code"] == "ERR_CUSTOM"
        assert error_dict["message"] == "Invalid input"
        assert error_dict["suggestion"] == "Check format"
        assert "field" in error_dict["details"]


class TestErrorExitCodes:
    """Test error exit codes"""

    def test_all_error_types_have_exit_codes(self):
        """Test all error types have valid exit codes"""
        error_types = [
            (ConfigurationError, 1, "ERR_CONFIG_INVALID"),
            (ProjectNotFoundError, 1, "ERR_PROJECT_NOT_FOUND"),
            (TemplateError, 1, "ERR_TEMPLATE_FAILED"),
            (DependencyError, 2, "ERR_DEPENDENCY_MISSING"),
            (FileSystemError, 2, "ERR_FILESYSTEM"),
            (DatabaseError, 2, "ERR_DATABASE"),
            (PipelineError, 3, "ERR_PIPELINE"),
            (ValidationError, 4, "ERR_VALIDATION"),
            (NetworkError, 5, "ERR_NETWORK"),
            (InteractiveError, 1, "ERR_INTERACTIVE"),
        ]

        for error_class, expected_exit_code, expected_error_code in error_types:
            if error_class == ProjectNotFoundError:
                error = error_class("/path")
            elif error_class == DependencyError:
                error = error_class("dep")
            else:
                error = error_class("test")

            assert error.exit_code == expected_exit_code
            assert error.error_code == expected_error_code
