"""
Tests for SBDK pipeline reload module.

Tests cover:
- ExecutionResult status and duration tracking
- PipelineReloader initialization and reload logic
- Pipeline module execution
- dbt execution and error handling
- Integration with file watcher
- Error reporting and recovery
"""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from rich.console import Console

from sbdk.dev.reload import (
    ExecutionResult,
    ExecutionStatus,
    PipelineReloader,
    ReloadError,
)


class TestExecutionStatus:
    """Test execution status enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all expected status values exist."""
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"


class TestExecutionResult:
    """Test execution result."""

    def test_result_creation(self) -> None:
        """Test creating execution result."""
        start = datetime.now()
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            start_time=start
        )

        assert result.status == ExecutionStatus.SUCCESS
        assert result.start_time == start
        assert result.is_success() is True

    def test_failed_result(self) -> None:
        """Test failed execution result."""
        result = ExecutionResult(
            status=ExecutionStatus.FAILED,
            start_time=datetime.now(),
            error="Test error"
        )

        assert result.is_success() is False
        assert result.error == "Test error"

    def test_duration_calculation(self) -> None:
        """Test duration tracking."""
        start = datetime.now()
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            start_time=start,
            duration=1.5
        )

        assert result.duration == 1.5
        assert result.get_duration_str() == "1.50s"

    def test_duration_unknown(self) -> None:
        """Test unknown duration."""
        result = ExecutionResult(
            status=ExecutionStatus.FAILED,
            start_time=datetime.now()
        )

        assert result.get_duration_str() == "unknown"

    def test_result_with_all_fields(self) -> None:
        """Test result with all fields."""
        start = datetime.now()
        end = datetime.now()

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            start_time=start,
            end_time=end,
            duration=2.5,
            output="Pipeline output"
        )

        assert result.start_time == start
        assert result.end_time == end
        assert result.duration == 2.5
        assert result.output == "Pipeline output"


class TestPipelineReloader:
    """Test pipeline reloader."""

    def test_initialization(self) -> None:
        """Test reloader initialization."""
        reloader = PipelineReloader(
            config_path="test_config.json",
            quiet=True
        )

        assert reloader.config_path == "test_config.json"
        assert reloader.quiet is True
        assert reloader.execution_count == 0

    def test_initialization_with_options(self) -> None:
        """Test initialization with various options."""
        reloader = PipelineReloader(
            pipelines_only=True,
            dbt_only=False,
            verbose=True
        )

        assert reloader.pipelines_only is True
        assert reloader.dbt_only is False
        assert reloader.verbose is True

    def test_missing_config_file(self) -> None:
        """Test reload with missing config file."""
        reloader = PipelineReloader(config_path="/nonexistent/config.json")

        with pytest.raises(ReloadError) as exc_info:
            reloader.reload()

        assert "Configuration file not found" in exc_info.value.message

    def test_reload_increments_counter(self) -> None:
        """Test that reload increments execution counter."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_execute_reload") as mock_execute:
                mock_execute.return_value = ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    start_time=datetime.now()
                )

                reloader = PipelineReloader(quiet=True)
                reloader.reload()
                assert reloader.execution_count == 1

                reloader.reload()
                assert reloader.execution_count == 2

    def test_reload_stores_result(self) -> None:
        """Test that reload stores last result."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_execute_reload") as mock_execute:
                result = ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    start_time=datetime.now(),
                    duration=1.0
                )
                mock_execute.return_value = result

                reloader = PipelineReloader(quiet=True)
                returned = reloader.reload()

                assert reloader.get_last_result() == result
                assert returned == result

    def test_reload_handles_exceptions(self) -> None:
        """Test exception handling in reload."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_execute_reload") as mock_execute:
                mock_execute.side_effect = Exception("Test error")

                reloader = PipelineReloader(quiet=True)
                result = reloader.reload()

                assert result.status == ExecutionStatus.FAILED
                assert "Test error" in result.error

    @patch("sbdk.dev.reload.Path.exists")
    def test_run_pipelines_no_directory(self, mock_exists: Mock) -> None:
        """Test when pipelines directory doesn't exist."""
        mock_exists.return_value = False

        reloader = PipelineReloader(quiet=True)
        # Should not raise
        reloader._run_pipelines()

    @patch("sbdk.dev.reload.Path.glob")
    @patch("sbdk.dev.reload.Path.exists")
    def test_run_pipelines_success(self, mock_exists: Mock, mock_glob: Mock) -> None:
        """Test successful pipeline execution."""
        mock_exists.return_value = True
        mock_glob.return_value = []

        reloader = PipelineReloader(quiet=True)
        # Should not raise with no pipeline files
        reloader._run_pipelines()

    @patch("subprocess.run")
    def test_run_dbt_success(self, mock_run: Mock) -> None:
        """Test successful dbt execution."""
        mock_run.return_value = MagicMock(returncode=0)

        reloader = PipelineReloader(quiet=True)
        # Should not raise
        reloader._run_dbt()

        # Verify dbt commands were called
        assert mock_run.call_count == 2  # deps and run

    @patch("subprocess.run")
    def test_run_dbt_not_found(self, mock_run: Mock) -> None:
        """Test dbt not found error."""
        mock_run.side_effect = FileNotFoundError("dbt not found")

        reloader = PipelineReloader(quiet=True)

        with pytest.raises(ReloadError) as exc_info:
            reloader._run_dbt()

        assert "dbt executable not found" in exc_info.value.message

    @patch("subprocess.run")
    def test_run_dbt_failure(self, mock_run: Mock) -> None:
        """Test dbt execution failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "dbt")

        reloader = PipelineReloader(quiet=True)

        with pytest.raises(ReloadError) as exc_info:
            reloader._run_dbt()

        assert "dbt execution failed" in exc_info.value.message

    def test_pipelines_only_mode(self) -> None:
        """Test pipelines-only mode."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_run_pipelines") as mock_pipelines:
                with patch.object(PipelineReloader, "_run_dbt") as mock_dbt:
                    mock_pipelines.return_value = None
                    mock_dbt.return_value = None

                    reloader = PipelineReloader(
                        pipelines_only=True,
                        quiet=True
                    )
                    reloader.reload()

                    # Only pipelines should be called
                    mock_pipelines.assert_called()

    def test_dbt_only_mode(self) -> None:
        """Test dbt-only mode."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_run_pipelines") as mock_pipelines:
                with patch.object(PipelineReloader, "_run_dbt") as mock_dbt:
                    mock_pipelines.return_value = None
                    mock_dbt.return_value = None

                    reloader = PipelineReloader(
                        dbt_only=True,
                        quiet=True
                    )
                    reloader.reload()

                    # Only dbt should be called
                    mock_dbt.assert_called()

    def test_get_execution_count(self) -> None:
        """Test getting execution count."""
        reloader = PipelineReloader()

        assert reloader.get_execution_count() == 0

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_execute_reload") as mock_execute:
                mock_execute.return_value = ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    start_time=datetime.now()
                )

                reloader.reload()
                assert reloader.get_execution_count() == 1

    def test_verbose_mode_output(self) -> None:
        """Test verbose mode output."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("sbdk.dev.reload.Console") as mock_console:
                reloader = PipelineReloader(
                    verbose=True,
                    console=mock_console
                )

                # Verify console is used
                assert reloader.console is mock_console

    def test_quiet_mode_suppresses_output(self) -> None:
        """Test quiet mode suppresses output."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_execute_reload") as mock_execute:
                mock_execute.return_value = ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    start_time=datetime.now()
                )

                reloader = PipelineReloader(quiet=True)
                # Should not raise
                reloader.reload()


class TestPipelineModuleExecution:
    """Test pipeline module execution."""

    def test_run_pipeline_module_success(self, tmp_path: Path) -> None:
        """Test successful pipeline module execution."""
        # Create a simple test module
        module_file = tmp_path / "test_pipeline.py"
        module_file.write_text("def run(): pass")

        reloader = PipelineReloader(quiet=True)

        # Should not raise
        reloader._run_pipeline_module(module_file)

    def test_run_pipeline_module_invalid(self, tmp_path: Path) -> None:
        """Test execution of invalid module."""
        module_file = tmp_path / "invalid.py"
        module_file.write_text("this is not valid python syntax {")

        reloader = PipelineReloader(quiet=True)

        with pytest.raises(ReloadError) as exc_info:
            reloader._run_pipeline_module(module_file)

        assert "Error executing" in exc_info.value.message

    def test_run_pipeline_module_missing(self, tmp_path: Path) -> None:
        """Test execution of missing module."""
        module_file = tmp_path / "missing.py"

        reloader = PipelineReloader(quiet=True)

        with pytest.raises(ReloadError):
            reloader._run_pipeline_module(module_file)


class TestReloadErrorHandling:
    """Test error handling in reload."""

    def test_reload_error_attributes(self) -> None:
        """Test ReloadError attributes."""
        error = ReloadError(
            message="Test error",
            suggestion="Do this instead"
        )

        assert error.message == "Test error"
        assert error.suggestion == "Do this instead"
        assert error.exit_code == 3

    def test_reload_error_to_dict(self) -> None:
        """Test converting error to dict."""
        error = ReloadError(
            message="Test error",
            suggestion="Try this",
            details={"key": "value"}
        )

        error_dict = error.to_dict()
        assert error_dict["error_type"] == "ReloadError"
        assert error_dict["message"] == "Test error"
        assert error_dict["suggestion"] == "Try this"
        assert error_dict["details"]["key"] == "value"


class TestIntegration:
    """Integration tests for reloader."""

    def test_full_reload_cycle(self, tmp_path: Path) -> None:
        """Test full reload cycle."""
        # Create config file
        config_file = tmp_path / "sbdk_config.json"
        config_file.write_text("{}")

        # Create pipelines directory
        pipelines_dir = tmp_path / "pipelines"
        pipelines_dir.mkdir()

        # Create a pipeline file
        pipeline_file = pipelines_dir / "test.py"
        pipeline_file.write_text("print('Pipeline executed')")

        # Run reload
        reloader = PipelineReloader(
            config_path=str(config_file),
            pipelines_only=True,
            quiet=True
        )

        result = reloader.reload()
        assert result.is_success()
        assert reloader.get_execution_count() == 1

    @patch("subprocess.run")
    def test_reload_with_dbt(self, mock_run: Mock) -> None:
        """Test reload with dbt."""
        mock_run.return_value = MagicMock(returncode=0)

        with patch("pathlib.Path.exists") as mock_exists:
            # Config exists, pipelines dir doesn't
            mock_exists.side_effect = lambda x=None: str(x) != "pipelines"

            reloader = PipelineReloader(
                dbt_only=True,
                quiet=True
            )

            result = reloader.reload()
            # Will fail because config file check happens first
            # but dbt operations will be attempted

    def test_multiple_reloads(self) -> None:
        """Test multiple consecutive reloads."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(PipelineReloader, "_execute_reload") as mock_execute:
                result = ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    start_time=datetime.now(),
                    duration=0.5
                )
                mock_execute.return_value = result

                reloader = PipelineReloader(quiet=True)

                for i in range(3):
                    r = reloader.reload()
                    assert r.is_success()
                    assert reloader.get_execution_count() == i + 1
