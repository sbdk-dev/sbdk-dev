"""
Pipeline Reload Logic for SBDK Hot-Reload Development Mode

Implements the reload execution engine with smart change detection,
execution status tracking, and clear developer feedback.

This module handles:
- Pipeline execution with status tracking
- Error recovery and reporting
- Execution timing and performance metrics
- Integration with watch mode
"""

import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from sbdk.exceptions import PipelineError, SBDKError


class ReloadError(SBDKError):
    """Raised when pipeline reload fails."""

    exit_code = 3


class ExecutionStatus(str, Enum):
    """Pipeline execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """
    Result of a pipeline execution.

    Attributes:
        status: Execution status
        start_time: When execution started
        end_time: When execution ended
        duration: Total execution time in seconds
        error: Error message if failed
        output: Captured output
    """

    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    output: Optional[str] = None

    def is_success(self) -> bool:
        """Check if execution succeeded."""
        return self.status == ExecutionStatus.SUCCESS

    def get_duration_str(self) -> str:
        """Get formatted duration."""
        if self.duration is None:
            return "unknown"
        return f"{self.duration:.2f}s"


class PipelineReloader:
    """
    Manages pipeline reload execution and status.

    Handles the core logic of detecting changes and triggering pipeline
    reloads with clear feedback and error handling.

    Example:
        >>> reloader = PipelineReloader(config_path="sbdk_config.json")
        >>> result = reloader.reload()
        >>> if result.is_success():
        ...     print("Pipeline reloaded successfully")
    """

    def __init__(
        self,
        config_path: str = "sbdk_config.json",
        pipelines_only: bool = False,
        dbt_only: bool = False,
        quiet: bool = False,
        verbose: bool = False,
        console: Optional[Console] = None
    ) -> None:
        """
        Initialize pipeline reloader.

        Args:
            config_path: Path to SBDK configuration file
            pipelines_only: Skip dbt transformations
            dbt_only: Skip pipeline execution
            quiet: Suppress non-essential output
            verbose: Show detailed execution information
            console: Rich console for output
        """
        self.config_path = config_path
        self.pipelines_only = pipelines_only
        self.dbt_only = dbt_only
        self.quiet = quiet
        self.verbose = verbose
        self.console = console or Console()

        self.last_result: Optional[ExecutionResult] = None
        self.execution_count = 0

    def reload(self) -> ExecutionResult:
        """
        Execute pipeline reload.

        Returns:
            ExecutionResult with status and details

        Raises:
            ReloadError: If reload configuration is invalid
        """
        start_time = datetime.now()
        self.execution_count += 1

        if not self.quiet and self.execution_count > 1:
            self.console.print("")  # Blank line for readability

        try:
            # Validate configuration
            if not Path(self.config_path).exists():
                raise ReloadError(
                    f"Configuration file not found: {self.config_path}",
                    suggestion="Run 'sbdk init' to create a project configuration"
                )

            # Execute reload
            result = self._execute_reload(start_time)
            self.last_result = result

            return result

        except ReloadError:
            raise
        except Exception as e:
            result = ExecutionResult(
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
            self.last_result = result
            return result

    def _execute_reload(self, start_time: datetime) -> ExecutionResult:
        """
        Internal method to execute reload steps.

        Args:
            start_time: When execution started

        Returns:
            ExecutionResult

        Raises:
            ReloadError: If any execution step fails
        """
        try:
            # Run pipelines if not skipped
            if not self.dbt_only:
                self._run_pipelines()

            # Run dbt if not skipped
            if not self.pipelines_only:
                self._run_dbt()

            # Success
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if not self.quiet:
                self._report_success(duration)

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if not self.quiet:
                self._report_failure(str(e), duration)

            raise ReloadError(
                f"Pipeline execution failed: {e}",
                suggestion="Check pipeline logs for detailed error information"
            ) from e

    def _run_pipelines(self) -> None:
        """
        Execute pipeline modules.

        Raises:
            ReloadError: If pipeline execution fails
        """
        pipelines_dir = Path("pipelines")

        if not pipelines_dir.exists():
            if self.verbose:
                self.console.print(
                    "[yellow]⚠️  No pipelines directory found[/yellow]"
                )
            return

        if not self.quiet:
            self.console.print("[cyan]Running pipelines...[/cyan]")

        pipeline_files = sorted(pipelines_dir.glob("*.py"))
        if not pipeline_files:
            if self.verbose:
                self.console.print(
                    "[yellow]⚠️  No pipeline files found[/yellow]"
                )
            return

        for pipeline_file in pipeline_files:
            if pipeline_file.name.startswith("_"):
                continue

            try:
                self._run_pipeline_module(pipeline_file)
            except Exception as e:
                raise ReloadError(
                    f"Pipeline '{pipeline_file.name}' failed: {e}",
                    suggestion=f"Check {pipeline_file} for errors"
                ) from e

    def _run_pipeline_module(self, module_path: Path) -> None:
        """
        Execute a single pipeline module.

        Args:
            module_path: Path to pipeline Python file

        Raises:
            ReloadError: If module execution fails
        """
        import importlib.util

        module_name = module_path.stem

        try:
            spec = importlib.util.spec_from_file_location(
                module_name,
                module_path
            )

            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if not self.quiet:
                    self.console.print(
                        f"[green]✅ {module_name}[/green]"
                    )
            else:
                raise ReloadError(
                    f"Failed to load module spec for {module_name}",
                    suggestion="Ensure the Python file is valid"
                )

        except Exception as e:
            raise ReloadError(
                f"Error executing {module_name}: {e}",
                suggestion="Check the pipeline for syntax errors"
            ) from e

    def _run_dbt(self) -> None:
        """
        Execute dbt transformations.

        Raises:
            ReloadError: If dbt execution fails
        """
        try:
            if not self.quiet:
                self.console.print("[cyan]Running dbt...[/cyan]")

            # Run dbt deps
            subprocess.run(
                ["dbt", "deps"],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Run dbt run
            subprocess.run(
                ["dbt", "run"],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            if not self.quiet:
                self.console.print("[green]✅ dbt[/green]")

        except subprocess.CalledProcessError as e:
            raise ReloadError(
                f"dbt execution failed",
                suggestion="Run 'dbt debug' to check configuration"
            ) from e

        except FileNotFoundError:
            raise ReloadError(
                "dbt executable not found",
                suggestion="Install dbt: pip install dbt-core dbt-duckdb"
            )

    def _report_success(self, duration: float) -> None:
        """
        Report successful execution.

        Args:
            duration: Execution time in seconds
        """
        self.console.print(
            Panel(
                f"[green]✅ Reload completed in {duration:.2f}s[/green]",
                style="green",
                expand=False
            )
        )

    def _report_failure(self, error: str, duration: float) -> None:
        """
        Report failed execution.

        Args:
            error: Error message
            duration: Execution time in seconds
        """
        self.console.print(
            Panel(
                f"[red]❌ Reload failed in {duration:.2f}s[/red]\n"
                f"[yellow]{error}[/yellow]",
                style="red",
                expand=False
            )
        )

    def get_last_result(self) -> Optional[ExecutionResult]:
        """Get the last execution result."""
        return self.last_result

    def get_execution_count(self) -> int:
        """Get total number of executions."""
        return self.execution_count
