"""
Unit tests for Phase 1: Formatters Module
Tests output formatting in multiple formats
"""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from sbdk.formatters import (
    OutputFormat,
    OutputFormatter,
    create_formatter
)


class TestOutputFormat:
    """Test OutputFormat enum"""

    def test_output_formats(self):
        """Test all output format values"""
        assert OutputFormat.TEXT == "text"
        assert OutputFormat.JSON == "json"
        assert OutputFormat.YAML == "yaml"
        assert OutputFormat.TABLE == "table"
        assert OutputFormat.MINIMAL == "minimal"


class TestOutputFormatterCreation:
    """Test OutputFormatter creation"""

    def test_create_default_formatter(self):
        """Test creating formatter with defaults"""
        formatter = OutputFormatter()

        assert formatter.format == OutputFormat.TEXT
        assert formatter.quiet is False
        assert formatter.console is not None

    def test_create_formatter_with_format(self):
        """Test creating formatter with specific format"""
        formatter = OutputFormatter(format=OutputFormat.JSON)

        assert formatter.format == OutputFormat.JSON

    def test_create_formatter_quiet_mode(self):
        """Test creating formatter in quiet mode"""
        formatter = OutputFormatter(quiet=True)

        assert formatter.quiet is True

    def test_create_formatter_function(self):
        """Test create_formatter factory function"""
        formatter = create_formatter(format="json", quiet=True)

        assert formatter.format == OutputFormat.JSON
        assert formatter.quiet is True

    def test_create_formatter_invalid_format(self):
        """Test create_formatter with invalid format defaults to TEXT"""
        formatter = create_formatter(format="invalid")

        assert formatter.format == OutputFormat.TEXT


class TestSuccessOutput:
    """Test success message formatting"""

    def test_success_text_format(self):
        """Test success in text format"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.success("Operation completed")

        output = console.file.getvalue()
        assert "✅" in output
        assert "Operation completed" in output

    def test_success_with_details_text(self):
        """Test success with details in text format"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.success("Pipeline done", details={"records": 100, "duration": "5s"})

        output = console.file.getvalue()
        assert "Pipeline done" in output
        assert "records" in output.lower() or "Records" in output

    def test_success_json_format(self):
        """Test success in JSON format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.JSON, console=console)

        formatter.success("Test success", details={"key": "value"})

        output = console.file.getvalue()
        data = json.loads(output)

        assert data["status"] == "success"
        assert data["message"] == "Test success"
        assert data["details"]["key"] == "value"

    def test_success_minimal_format(self):
        """Test success in minimal format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.MINIMAL, console=console)

        formatter.success("Done")

        output = console.file.getvalue()
        assert "✅ Done" in output

    def test_success_quiet_mode(self):
        """Test success in quiet mode (no output)"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(quiet=True, console=console)

        formatter.success("This should not appear")

        output = console.file.getvalue()
        assert output == ""


class TestErrorOutput:
    """Test error message formatting"""

    def test_error_text_format(self):
        """Test error in text format"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.error("Something failed")

        output = console.file.getvalue()
        assert "❌" in output
        assert "Something failed" in output

    def test_error_with_suggestion(self):
        """Test error with suggestion"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.error("Failed", suggestion="Try again")

        output = console.file.getvalue()
        assert "Failed" in output
        assert "💡" in output
        assert "Try again" in output

    def test_error_json_format(self):
        """Test error in JSON format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.JSON, console=console)

        formatter.error("Test error", suggestion="Fix it", details={"code": 42})

        output = console.file.getvalue()
        data = json.loads(output)

        assert data["status"] == "error"
        assert data["message"] == "Test error"
        assert data["suggestion"] == "Fix it"
        assert data["details"]["code"] == 42

    def test_error_minimal_format(self):
        """Test error in minimal format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.MINIMAL, console=console)

        formatter.error("Error occurred")

        output = console.file.getvalue()
        assert "❌ Error occurred" in output


class TestInfoOutput:
    """Test info message formatting"""

    def test_info_text_format(self):
        """Test info in text format"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.info("Information message")

        output = console.file.getvalue()
        assert "Information message" in output

    def test_info_json_format(self):
        """Test info in JSON format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.JSON, console=console)

        formatter.info("Test info", details={"version": "1.0"})

        output = console.file.getvalue()
        data = json.loads(output)

        assert data["status"] == "info"
        assert data["message"] == "Test info"

    def test_info_quiet_mode(self):
        """Test info in quiet mode (suppressed)"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(quiet=True, console=console)

        formatter.info("This should be suppressed")

        output = console.file.getvalue()
        assert output == ""


class TestWarningOutput:
    """Test warning message formatting"""

    def test_warning_text_format(self):
        """Test warning in text format"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.warning("Warning message")

        output = console.file.getvalue()
        assert "⚠️" in output
        assert "Warning message" in output

    def test_warning_with_suggestion(self):
        """Test warning with suggestion"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.warning("Deprecated", suggestion="Use new API")

        output = console.file.getvalue()
        assert "Deprecated" in output
        assert "Use new API" in output

    def test_warning_json_format(self):
        """Test warning in JSON format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.JSON, console=console)

        formatter.warning("Test warning", suggestion="Update")

        output = console.file.getvalue()
        data = json.loads(output)

        assert data["status"] == "warning"
        assert data["message"] == "Test warning"

    def test_warning_quiet_mode(self):
        """Test warning in quiet mode (suppressed)"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(quiet=True, console=console)

        formatter.warning("Suppressed warning")

        output = console.file.getvalue()
        assert output == ""


class TestTableOutput:
    """Test table formatting"""

    def test_table_with_data(self):
        """Test table with data"""
        console = Console(file=StringIO(), force_terminal=True, width=120)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        data = [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"}
        ]

        formatter.table(data)

        output = console.file.getvalue()
        assert "Alice" in output
        assert "Bob" in output

    def test_table_json_format(self):
        """Test table in JSON format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.JSON, console=console)

        data = [{"name": "Alice", "age": 30}]

        formatter.table(data)

        output = console.file.getvalue()
        result = json.loads(output)

        assert result["data"] == data

    def test_table_minimal_format(self):
        """Test table in minimal format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.MINIMAL, console=console)

        data = [{"name": "Alice", "age": 30}]

        formatter.table(data)

        output = console.file.getvalue()
        assert "Alice" in output
        assert "30" in output

    def test_table_empty_data(self):
        """Test table with empty data"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        formatter.table([])

        output = console.file.getvalue()
        assert "No data" in output or "⚠️" in output

    def test_table_with_custom_columns(self):
        """Test table with custom column list"""
        console = Console(file=StringIO(), force_terminal=True, width=120)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        data = [{"name": "Alice", "age": 30, "city": "NYC"}]

        formatter.table(data, columns=["name", "city"])

        output = console.file.getvalue()
        assert "Alice" in output
        assert "NYC" in output


class TestDictOutput:
    """Test dictionary output formatting"""

    def test_dict_text_format(self):
        """Test dict in text format"""
        console = Console(file=StringIO(), force_terminal=True)
        formatter = OutputFormatter(format=OutputFormat.TEXT, console=console)

        data = {"key1": "value1", "key2": "value2"}

        formatter.dict_data(data)

        output = console.file.getvalue()
        assert "key1" in output or "Key1" in output
        assert "value1" in output

    def test_dict_json_format(self):
        """Test dict in JSON format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.JSON, console=console)

        data = {"key": "value"}

        formatter.dict_data(data)

        output = console.file.getvalue()
        result = json.loads(output)

        assert result["key"] == "value"

    def test_dict_table_format(self):
        """Test dict in table format"""
        console = Console(file=StringIO(), force_terminal=True, width=120)
        formatter = OutputFormatter(format=OutputFormat.TABLE, console=console)

        data = {"key1": "value1", "key2": "value2"}

        formatter.dict_data(data)

        output = console.file.getvalue()
        assert "key1" in output or "Key" in output
        assert "value1" in output or "Value" in output

    def test_dict_with_yaml_format(self):
        """Test dict in YAML format (if PyYAML available)"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.YAML, console=console)

        data = {"key": "value"}

        formatter.dict_data(data)

        output = console.file.getvalue()
        # Should contain YAML format or JSON fallback
        assert "key" in output


class TestListOutput:
    """Test list output formatting"""

    def test_list_basic(self):
        """Test basic list output"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(console=console)

        data = ["item1", "item2", "item3"]

        formatter.list_data(data)

        output = console.file.getvalue()
        assert "item1" in output
        assert "item2" in output
        assert "•" in output

    def test_list_numbered(self):
        """Test numbered list output"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(console=console)

        data = ["first", "second"]

        formatter.list_data(data, numbered=True)

        output = console.file.getvalue()
        assert "1." in output
        assert "2." in output
        assert "first" in output

    def test_list_with_title(self):
        """Test list with title"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(console=console)

        data = ["item1"]

        formatter.list_data(data, title="My List")

        output = console.file.getvalue()
        assert "My List" in output

    def test_list_json_format(self):
        """Test list in JSON format"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(format=OutputFormat.JSON, console=console)

        data = ["a", "b", "c"]

        formatter.list_data(data)

        output = console.file.getvalue()
        result = json.loads(output)

        assert result["items"] == data


class TestQuietMode:
    """Test quiet mode suppression"""

    def test_quiet_mode_suppresses_all_except_errors(self):
        """Test quiet mode only allows errors"""
        console = Console(file=StringIO())
        formatter = OutputFormatter(quiet=True, console=console)

        # These should be suppressed
        formatter.success("Success")
        formatter.info("Info")
        formatter.warning("Warning")

        output = console.file.getvalue()
        assert output == ""

        # Errors should still show (different test method needed for stderr)
