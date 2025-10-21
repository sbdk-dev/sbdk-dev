"""
Base Command Architecture for SBDK CLI

Provides abstract base class for all CLI commands with:
- Context management integration
- Structured error handling
- Output formatting
- Dry-run support
- Validation

Inspired by spec-kit's command architecture patterns.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import typer

from sbdk.context import SBDKContext, create_context
from sbdk.exceptions import SBDKError, exit_with_error
from sbdk.formatters import OutputFormatter, create_formatter


class BaseCommand(ABC):
    """
    Abstract base class for all SBDK CLI commands.

    Provides common functionality:
    - Context management
    - Error handling
    - Output formatting
    - Validation
    - Dry-run support

    Commands should inherit from this class and implement:
    - validate(): Pre-execution validation
    - execute(): Main command logic
    """

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        verbose: bool = False,
        quiet: bool = False,
        dry_run: bool = False,
        output_format: str = "text"
    ):
        """
        Initialize base command.

        Args:
            project_dir: Project directory (default: current directory)
            verbose: Enable verbose output
            quiet: Suppress non-essential output
            dry_run: Preview actions without executing
            output_format: Output format (text, json, yaml, table, minimal)
        """
        self.project_dir = project_dir or Path.cwd()
        self.verbose = verbose
        self.quiet = quiet
        self.dry_run = dry_run
        self.output_format = output_format

        # Initialize context
        self.ctx = create_context(
            project_dir=self.project_dir,
            verbose=verbose,
            quiet=quiet,
            dry_run=dry_run
        )

        # Initialize formatter
        self.formatter = create_formatter(
            format=output_format,
            console=self.ctx.console,
            quiet=quiet
        )

    @abstractmethod
    def validate(self) -> None:
        """
        Validate command preconditions.

        Should raise ValidationError if validation fails.
        Called before execute().
        """
        pass

    @abstractmethod
    def execute(self) -> dict[str, Any]:
        """
        Execute the command.

        Returns:
            Dictionary with execution results

        Raises:
            SBDKError: If execution fails
        """
        pass

    def run(self) -> None:
        """
        Run the complete command lifecycle.

        Handles:
        1. Validation
        2. Execution
        3. Output formatting
        4. Error handling
        5. Cleanup
        """
        try:
            # Pre-execution validation
            if self.verbose:
                self.ctx.logger.debug(f"Validating {self.__class__.__name__}...")

            self.validate()

            # Execute command
            if self.verbose:
                self.ctx.logger.debug(f"Executing {self.__class__.__name__}...")

            if self.dry_run:
                self.formatter.info(
                    f"[DRY RUN] Would execute: {self.__class__.__name__}",
                    title="Dry Run Mode"
                )
                return

            result = self.execute()

            # Format output
            if result:
                self._format_result(result)

        except SBDKError as e:
            # Structured error handling
            self.formatter.error(
                e.message,
                suggestion=e.suggestion,
                details=e.details if self.verbose else None
            )
            exit_with_error(e, verbose=self.verbose)

        except Exception as e:
            # Unexpected errors
            self.ctx.logger.exception("Unexpected error")
            self.formatter.error(
                f"Unexpected error: {str(e)}",
                suggestion="Run with --verbose for detailed traceback"
            )
            raise typer.Exit(1) from e

        finally:
            # Cleanup
            self.ctx.cleanup()

    def _format_result(self, result: dict[str, Any]) -> None:
        """
        Format and display command result.

        Args:
            result: Command execution result
        """
        if "success" in result and result["success"]:
            self.formatter.success(
                result.get("message", "Command completed successfully"),
                details=result.get("details")
            )
        elif "error" in result:
            self.formatter.error(
                result.get("message", "Command failed"),
                suggestion=result.get("suggestion")
            )
        else:
            # Generic output
            self.formatter.dict_data(result)


class ProjectCommand(BaseCommand):
    """
    Base class for commands that require an SBDK project.

    Automatically verifies project structure exists.
    """

    def validate(self) -> None:
        """
        Validate project structure exists.

        Raises:
            ProjectNotFoundError: If not in a valid SBDK project
        """
        self.ctx.verify_project_structure()


class InitCommand(BaseCommand):
    """
    Base class for initialization commands.

    Does not require existing project structure.
    """

    def validate(self) -> None:
        """
        Minimal validation for init commands.

        Can be overridden by subclasses for additional validation.
        """
        pass


# Utility decorators for command functions

def with_context(
    verbose: bool = False,
    quiet: bool = False,
    dry_run: bool = False,
    output_format: str = "text"
):
    """
    Decorator to inject SBDK context into command functions.

    Usage:
        @with_context(verbose=True)
        def my_command(ctx: SBDKContext, ...):
            ctx.logger.info("Command running...")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            ctx = create_context(
                verbose=verbose,
                quiet=quiet,
                dry_run=dry_run
            )
            try:
                return func(ctx=ctx, *args, **kwargs)
            finally:
                ctx.cleanup()
        return wrapper
    return decorator


def handle_errors(func):
    """
    Decorator to handle errors in command functions.

    Catches SBDKError and formats appropriately.

    Usage:
        @handle_errors
        def my_command(...):
            # Command logic
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SBDKError as e:
            from rich.console import Console
            console = Console(stderr=True)

            formatter = create_formatter(console=console)
            formatter.error(
                e.message,
                suggestion=e.suggestion,
                details=e.details
            )
            exit_with_error(e)
        except Exception as e:
            from rich.console import Console
            console = Console(stderr=True)

            console.print(f"[red]Unexpected error: {e}[/red]")
            raise typer.Exit(1) from e

    return wrapper
