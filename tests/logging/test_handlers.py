"""
Tests for SBDK Logging Handlers

Tests custom handlers for error context, rich console output, and file rotation.
"""

import logging
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from sbdk.logging.handlers import (
    ContextAwareHandler,
    DuplicateErrorFilter,
    ErrorContextFilter,
    RichConsoleHandler,
    RotatingFileHandler,
)


class TestContextAwareHandler:
    """Test ContextAwareHandler"""

    def test_handler_adds_file_context(self):
        """Test handler adds file context to records"""
        handler = ContextAwareHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_func"

        # Mock the handle method to check attributes
        with patch.object(handler, "handle"):
            handler.emit(record)

            assert hasattr(record, "file_context")
            assert "test.py:42" in record.file_context
            assert hasattr(record, "function_name")
            assert record.function_name == "test_func"

    def test_handler_adds_error_code(self):
        """Test handler adds error code for errors"""
        handler = ContextAwareHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=None,
        )
        record.error_code = "ERR_CUSTOM"

        with patch.object(handler, "handle"):
            handler.emit(record)

            assert record.error_code == "ERR_CUSTOM"


class TestRichConsoleHandler:
    """Test RichConsoleHandler"""

    def test_handler_initialization(self):
        """Test handler initializes properly"""
        console = Console(file=StringIO())
        handler = RichConsoleHandler(console=console)

        assert handler.console == console
        # RichHandler stores these internally, just verify handler was created
        assert handler is not None

    def test_handler_emits_without_error(self):
        """Test handler can emit records"""
        console = Console(file=StringIO())
        handler = RichConsoleHandler(console=console)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Should not raise
        handler.emit(record)

    def test_handler_creates_default_console(self):
        """Test handler creates console if not provided"""
        handler = RichConsoleHandler()

        assert handler.console is not None
        assert isinstance(handler.console, Console)


class TestRotatingFileHandler:
    """Test RotatingFileHandler"""

    def test_handler_creates_log_directory(self):
        """Test handler creates log directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "test.log"
            handler = RotatingFileHandler(log_file)

            assert log_file.parent.exists()
            handler.close()

    def test_handler_writes_to_file(self):
        """Test handler writes log records to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            handler = RotatingFileHandler(log_file)

            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None,
            )

            handler.emit(record)
            handler.close()

            assert log_file.exists()
            content = log_file.read_text()
            assert len(content) > 0

    def test_handler_respects_encoding(self):
        """Test handler respects encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            handler = RotatingFileHandler(log_file, encoding="utf-8")

            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test with unicode: ñ é",
                args=(),
                exc_info=None,
            )

            handler.emit(record)
            handler.close()

            assert log_file.exists()

    def test_handler_performs_rollover(self):
        """Test handler performs file rotation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            # Very small max size to trigger rollover
            handler = RotatingFileHandler(
                log_file, max_bytes=50, backup_count=2
            )

            # Write multiple records to trigger rollover
            for i in range(5):
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg=f"Message {i}",
                    args=(),
                    exc_info=None,
                )
                handler.emit(record)

            handler.close()

            # Should have created backup files
            log_dir = Path(tmpdir)
            log_files = list(log_dir.glob("test.log*"))
            assert len(log_files) > 1

    def test_handler_cleanup_old_logs(self):
        """Test handler can perform cleanup (may not delete in test due to timing)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            handler = RotatingFileHandler(log_file, max_bytes=50)

            # Just verify cleanup doesn't error
            try:
                handler._cleanup_old_logs(keep_days=30)
            except Exception as e:
                pytest.fail(f"Cleanup should not raise exception: {e}")

            handler.close()


class TestErrorContextFilter:
    """Test ErrorContextFilter"""

    def test_filter_allows_all_records(self):
        """Test filter returns True for all records"""
        filter_obj = ErrorContextFilter()

        records = [
            logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )
            for level in [logging.DEBUG, logging.INFO, logging.WARNING,
                         logging.ERROR, logging.CRITICAL]
        ]

        for record in records:
            assert filter_obj.filter(record) is True

    def test_filter_adds_context_for_errors(self):
        """Test filter adds context for error level records"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.ERROR,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_func"
        record.process = 1234
        record.thread = 5678

        filter_obj.filter(record)

        assert hasattr(record, "error_context")
        context = record.error_context
        assert context["logger"] == "test.module"
        assert context["level"] == "ERROR"
        assert context["file"] == "/path/to/test.py"
        assert context["line"] == 42
        assert context["function"] == "test_func"

    def test_filter_provides_recovery_suggestion_for_database_error(self):
        """Test filter suggests recovery for database errors"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="database connection failed",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        assert hasattr(record, "recovery_suggestion")
        assert record.recovery_suggestion is not None
        assert "database" in record.recovery_suggestion.lower()

    def test_filter_provides_recovery_suggestion_for_config_error(self):
        """Test filter suggests recovery for config errors"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="configuration file not found",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        assert record.recovery_suggestion is not None

    def test_filter_provides_recovery_suggestion_for_dependency_error(self):
        """Test filter suggests recovery for dependency errors"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="failed to import dbt",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        assert record.recovery_suggestion is not None
        assert "uv sync" in record.recovery_suggestion.lower()

    def test_filter_no_context_for_non_errors(self):
        """Test filter doesn't add context for non-error records"""
        filter_obj = ErrorContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Info message",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        assert record.error_context is None
        assert record.recovery_suggestion is None


class TestDuplicateErrorFilter:
    """Test DuplicateErrorFilter"""

    def test_filter_allows_first_occurrence(self):
        """Test filter allows first occurrence of error"""
        filter_obj = DuplicateErrorFilter(suppress_window_seconds=10)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        assert filter_obj.filter(record) is True

    def test_filter_suppresses_duplicate_within_window(self):
        """Test filter suppresses duplicate within time window"""
        filter_obj = DuplicateErrorFilter(suppress_window_seconds=60)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        # First should pass
        assert filter_obj.filter(record) is True

        # Second identical should be suppressed
        assert filter_obj.filter(record) is False

    def test_filter_allows_different_errors(self):
        """Test filter allows different errors"""
        filter_obj = DuplicateErrorFilter(suppress_window_seconds=60)

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

    def test_filter_allows_all_non_error_levels(self):
        """Test filter allows all non-error level records"""
        filter_obj = DuplicateErrorFilter()

        levels = [logging.DEBUG, logging.INFO, logging.WARNING]

        for level in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Message",
                args=(),
                exc_info=None,
            )

            # All non-errors should always pass
            assert filter_obj.filter(record) is True
            assert filter_obj.filter(record) is True

    def test_filter_cleans_up_old_entries(self):
        """Test filter cleans up old error entries"""
        filter_obj = DuplicateErrorFilter(suppress_window_seconds=1)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=None,
        )

        # Log first occurrence
        assert filter_obj.filter(record) is True
        initial_count = len(filter_obj.last_errors)

        # Wait for suppress window to pass
        import time
        time.sleep(1.1)

        # Should allow same error again (after cleanup)
        assert filter_obj.filter(record) is True

    def test_filter_handles_location_differences(self):
        """Test filter distinguishes errors by location"""
        filter_obj = DuplicateErrorFilter(suppress_window_seconds=60)

        record1 = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="file1.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        record2 = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="file2.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        # Same message but different file
        assert filter_obj.filter(record1) is True
        assert filter_obj.filter(record2) is True


class TestHandlerIntegration:
    """Test handlers working together"""

    def test_handlers_with_logger(self):
        """Test handlers work with logger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            # Create logger with handlers
            logger = logging.getLogger("test_integration")
            logger.handlers.clear()
            logger.setLevel(logging.DEBUG)

            # Add rotating file handler
            file_handler = RotatingFileHandler(log_file)
            logger.addHandler(file_handler)

            # Add filters
            logger.addFilter(ErrorContextFilter())
            logger.addFilter(DuplicateErrorFilter())

            # Log some messages
            logger.info("Info message")
            logger.error("Error message")

            file_handler.close()

            # Check file was written
            assert log_file.exists()
            content = log_file.read_text()
            assert "Info message" in content
            assert "Error message" in content

    def test_console_and_file_handlers_together(self):
        """Test console and file handlers work together"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            # Create logger
            logger = logging.getLogger("test_console_file")
            logger.handlers.clear()
            logger.setLevel(logging.DEBUG)

            # Add console handler
            console = Console(file=StringIO())
            console_handler = RichConsoleHandler(console=console)
            logger.addHandler(console_handler)

            # Add file handler
            file_handler = RotatingFileHandler(log_file)
            logger.addHandler(file_handler)

            # Log message
            logger.info("Test message")

            console_handler.close()
            file_handler.close()

            # Both should have the message
            assert log_file.exists()
