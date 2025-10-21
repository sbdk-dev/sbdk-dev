"""
SBDK Output Formatters

Structured output formatting for CLI commands supporting multiple output formats:
- text: Human-readable rich text (default)
- json: Machine-readable JSON
- yaml: YAML format for configuration files
- table: Tabular data display
- minimal: Minimal output for scripting

Inspired by spec-kit's clean, structured output patterns.
"""

import json
from enum import Enum
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class OutputFormat(str, Enum):
    """Supported output formats."""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    TABLE = "table"
    MINIMAL = "minimal"


class OutputFormatter:
    """
    Centralized output formatting for CLI commands.

    Handles formatting and display of command output in various formats
    based on user preference and command context.
    """

    def __init__(
        self,
        format: OutputFormat = OutputFormat.TEXT,
        console: Optional[Console] = None,
        quiet: bool = False
    ):
        """
        Initialize output formatter.

        Args:
            format: Output format to use
            console: Rich Console instance (creates new if None)
            quiet: Suppress all output except errors
        """
        self.format = format
        self.console = console or Console()
        self.quiet = quiet

    def success(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        title: str = "Success"
    ) -> None:
        """
        Display success message.

        Args:
            message: Success message
            details: Additional details dictionary
            title: Panel title for text format
        """
        if self.quiet:
            return

        if self.format == OutputFormat.JSON:
            self._output_json({
                "status": "success",
                "message": message,
                "details": details or {}
            })
        elif self.format == OutputFormat.TEXT:
            content = f"[green]✅ {message}[/green]"
            if details:
                content += "\n\n" + self._format_details(details)
            self.console.print(Panel(content, title=title, style="green"))
        elif self.format == OutputFormat.MINIMAL:
            self.console.print(f"✅ {message}")
        else:
            self.console.print(f"✅ {message}")
            if details:
                self._output_details(details)

    def error(
        self,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        title: str = "Error"
    ) -> None:
        """
        Display error message.

        Args:
            message: Error message
            suggestion: Suggested fix
            details: Additional error details
            title: Panel title for text format
        """
        if self.format == OutputFormat.JSON:
            self._output_json({
                "status": "error",
                "message": message,
                "suggestion": suggestion,
                "details": details or {}
            })
        elif self.format == OutputFormat.TEXT:
            content = f"[red]❌ {message}[/red]"
            if suggestion:
                content += f"\n\n[yellow]💡 Suggestion: {suggestion}[/yellow]"
            if details:
                content += "\n\n" + self._format_details(details)
            self.console.print(Panel(content, title=title, style="red"))
        elif self.format == OutputFormat.MINIMAL:
            # For minimal format, just print to console (errors always shown)
            self.console.print(f"❌ {message}")
        else:
            self.console.print(f"❌ {message}")
            if suggestion:
                self.console.print(f"💡 {suggestion}")
            if details:
                self._output_details(details)

    def info(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        title: Optional[str] = None
    ) -> None:
        """
        Display informational message.

        Args:
            message: Info message
            details: Additional details
            title: Panel title for text format
        """
        if self.quiet:
            return

        if self.format == OutputFormat.JSON:
            self._output_json({
                "status": "info",
                "message": message,
                "details": details or {}
            })
        elif self.format == OutputFormat.TEXT:
            content = f"[cyan]{message}[/cyan]"
            if details:
                content += "\n\n" + self._format_details(details)
            if title:
                self.console.print(Panel(content, title=title, style="cyan"))
            else:
                self.console.print(content)
        elif self.format == OutputFormat.MINIMAL:
            self.console.print(message)
        else:
            self.console.print(message)
            if details:
                self._output_details(details)

    def warning(
        self,
        message: str,
        suggestion: Optional[str] = None,
        title: str = "Warning"
    ) -> None:
        """
        Display warning message.

        Args:
            message: Warning message
            suggestion: Suggested action
            title: Panel title for text format
        """
        if self.quiet:
            return

        if self.format == OutputFormat.JSON:
            self._output_json({
                "status": "warning",
                "message": message,
                "suggestion": suggestion
            })
        elif self.format == OutputFormat.TEXT:
            content = f"[yellow]⚠️  {message}[/yellow]"
            if suggestion:
                content += f"\n\n[dim]💡 {suggestion}[/dim]"
            self.console.print(Panel(content, title=title, style="yellow"))
        elif self.format == OutputFormat.MINIMAL:
            self.console.print(f"⚠️  {message}")
        else:
            self.console.print(f"⚠️  {message}")
            if suggestion:
                self.console.print(f"💡 {suggestion}")

    def table(
        self,
        data: list[dict[str, Any]],
        columns: Optional[list[str]] = None,
        title: Optional[str] = None
    ) -> None:
        """
        Display data in table format.

        Args:
            data: List of dictionaries representing table rows
            columns: List of column names (uses first row keys if None)
            title: Table title
        """
        if self.quiet:
            return

        if not data:
            self.warning("No data to display")
            return

        if self.format == OutputFormat.JSON:
            self._output_json({"data": data})
            return

        if self.format == OutputFormat.MINIMAL:
            for row in data:
                self.console.print(" | ".join(str(v) for v in row.values()))
            return

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Create Rich table
        table = Table(title=title, show_header=True, header_style="bold cyan")

        for col in columns:
            table.add_column(col, style="dim")

        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])

        self.console.print(table)

    def dict_data(
        self,
        data: dict[str, Any],
        title: Optional[str] = None
    ) -> None:
        """
        Display dictionary data.

        Args:
            data: Dictionary to display
            title: Title for the output
        """
        if self.quiet:
            return

        if self.format == OutputFormat.JSON:
            self._output_json(data)
        elif self.format == OutputFormat.YAML:
            self._output_yaml(data)
        elif self.format == OutputFormat.TEXT:
            content = self._format_details(data)
            if title:
                self.console.print(Panel(content, title=title, style="cyan"))
            else:
                self.console.print(content)
        elif self.format == OutputFormat.TABLE:
            # Convert dict to table rows
            table_data = [{"Key": k, "Value": str(v)} for k, v in data.items()]
            self.table(table_data, title=title)
        else:
            for key, value in data.items():
                self.console.print(f"{key}: {value}")

    def list_data(
        self,
        data: list[Any],
        title: Optional[str] = None,
        numbered: bool = False
    ) -> None:
        """
        Display list data.

        Args:
            data: List to display
            title: Title for the output
            numbered: Show numbered list
        """
        if self.quiet:
            return

        if self.format == OutputFormat.JSON:
            self._output_json({"items": data})
        elif self.format == OutputFormat.YAML:
            self._output_yaml({"items": data})
        else:
            if title:
                self.console.print(f"\n[bold]{title}[/bold]")

            for idx, item in enumerate(data, 1):
                if numbered:
                    self.console.print(f"  {idx}. {item}")
                else:
                    self.console.print(f"  • {item}")

    def _output_json(self, data: dict[str, Any]) -> None:
        """Output data as JSON."""
        self.console.print(json.dumps(data, indent=2, default=str))

    def _output_yaml(self, data: dict[str, Any]) -> None:
        """Output data as YAML."""
        try:
            import yaml
            self.console.print(yaml.dump(data, default_flow_style=False, sort_keys=False))
        except ImportError:
            # Fallback to JSON if YAML not available
            self._output_json(data)

    def _format_details(self, details: dict[str, Any]) -> str:
        """Format details dictionary for text output."""
        lines = []
        for key, value in details.items():
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, dict):
                lines.append(f"[cyan]{formatted_key}:[/cyan]")
                for sub_key, sub_value in value.items():
                    lines.append(f"  • {sub_key}: {sub_value}")
            elif isinstance(value, list):
                lines.append(f"[cyan]{formatted_key}:[/cyan]")
                for item in value:
                    lines.append(f"  • {item}")
            else:
                lines.append(f"[cyan]{formatted_key}:[/cyan] {value}")
        return "\n".join(lines)

    def _output_details(self, details: dict[str, Any]) -> None:
        """Output details in current format."""
        if self.format == OutputFormat.JSON:
            self._output_json(details)
        elif self.format == OutputFormat.YAML:
            self._output_yaml(details)
        elif self.format == OutputFormat.TABLE:
            table_data = [{"Key": k, "Value": str(v)} for k, v in details.items()]
            self.table(table_data)
        else:
            for key, value in details.items():
                self.console.print(f"  {key}: {value}")


def create_formatter(
    format: Optional[str] = None,
    console: Optional[Console] = None,
    quiet: bool = False
) -> OutputFormatter:
    """
    Factory function to create OutputFormatter.

    Args:
        format: Output format string (text, json, yaml, table, minimal)
        console: Rich Console instance
        quiet: Suppress output

    Returns:
        Configured OutputFormatter instance
    """
    # Parse format string
    if format:
        try:
            output_format = OutputFormat(format.lower())
        except ValueError:
            output_format = OutputFormat.TEXT
    else:
        output_format = OutputFormat.TEXT

    return OutputFormatter(format=output_format, console=console, quiet=quiet)
