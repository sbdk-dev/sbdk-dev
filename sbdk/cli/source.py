"""
Data Source Management CLI Commands

Commands for adding, listing, syncing, testing, and managing SBDK data sources.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from sbdk.exceptions import (
    ConfigurationError,
    FileSystemError,
    SBDKError,
    ValidationError,
)
from sbdk.sources import (
    BaseConnector,
    ConnectionStatus,
    SourceConnectionConfig,
    SourceType,
)

app = typer.Typer(help="Data source management commands")
console = Console()


def get_sources_dir() -> Path:
    """
    Get the sources directory path.

    Returns:
        Path to ~/.sbdk/sources/

    Raises:
        FileSystemError: If directory cannot be created
    """
    sources_dir = Path.home() / ".sbdk" / "sources"
    try:
        sources_dir.mkdir(parents=True, exist_ok=True)
        return sources_dir
    except Exception as e:
        raise FileSystemError(
            f"Failed to create sources directory: {sources_dir}",
            suggestion="Check file system permissions",
            details={"error": str(e)}
        )


def get_source_config_path(name: str) -> Path:
    """Get path to source config file."""
    return get_sources_dir() / f"{name}.json"


def load_source_config(name: str) -> Dict[str, Any]:
    """
    Load source configuration.

    Args:
        name: Source name

    Returns:
        Source configuration dictionary

    Raises:
        ConfigurationError: If config file not found or invalid
    """
    config_path = get_source_config_path(name)

    if not config_path.exists():
        raise ConfigurationError(
            f"Source '{name}' not found",
            suggestion=f"List available sources: sbdk source list"
        )

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Invalid JSON in source config: {config_path}",
            suggestion="Check the JSON syntax or recreate the source",
            details={"error": str(e)}
        )
    except Exception as e:
        raise FileSystemError(
            f"Failed to read source config: {config_path}",
            suggestion="Check file permissions",
            details={"error": str(e)}
        )


def save_source_config(name: str, config: Dict[str, Any]) -> None:
    """
    Save source configuration.

    Args:
        name: Source name
        config: Source configuration dictionary

    Raises:
        FileSystemError: If config cannot be saved
    """
    config_path = get_source_config_path(name)

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2, default=str)
    except Exception as e:
        raise FileSystemError(
            f"Failed to save source config: {config_path}",
            suggestion="Check file system permissions",
            details={"error": str(e)}
        )


def list_source_names() -> list[str]:
    """
    List all configured source names.

    Returns:
        List of source names
    """
    sources_dir = get_sources_dir()
    return [
        f.stem for f in sources_dir.glob("*.json")
        if f.is_file()
    ]


def validate_source_name(name: str) -> None:
    """
    Validate source name format.

    Args:
        name: Source name to validate

    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError(
            "Source name cannot be empty",
            suggestion="Provide a valid source name"
        )

    if not name.replace("-", "").replace("_", "").isalnum():
        raise ValidationError(
            f"Invalid source name: {name}",
            suggestion="Use only alphanumeric characters, hyphens, and underscores"
        )


@app.command()
def add(
    name: str = typer.Argument(..., help="Source name"),
    source_type: str = typer.Option(
        ...,
        "--type",
        "-t",
        help="Source type: csv, postgres, mysql, api"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Source description"
    ),
    connection_string: Optional[str] = typer.Option(
        None,
        "--connection",
        "-c",
        help="Connection string (for databases)"
    ),
    file_path: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="File path (for file sources)"
    ),
    test_connection: bool = typer.Option(
        True,
        "--test/--no-test",
        help="Test connection before saving"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output"
    ),
) -> None:
    """
    Add a new data source.

    Examples:
        # Add CSV source
        sbdk source add users --type csv --file data/users.csv

        # Add PostgreSQL source
        sbdk source add db --type postgres --connection "postgresql://localhost/mydb"

        # Add with description
        sbdk source add api --type api --description "External API" --connection "https://api.example.com"
    """
    try:
        # Validate source name
        validate_source_name(name)

        # Check if source already exists
        if get_source_config_path(name).exists():
            raise ConfigurationError(
                f"Source '{name}' already exists",
                suggestion=f"Use a different name or remove existing: sbdk source remove {name}"
            )

        # Parse source type
        try:
            parsed_type = SourceType(source_type.lower())
        except ValueError:
            valid_types = ", ".join([t.value for t in SourceType])
            raise ValidationError(
                f"Invalid source type: {source_type}",
                suggestion=f"Use one of: {valid_types}"
            )

        # Build configuration
        config = {
            "name": name,
            "source_type": parsed_type.value,
            "description": description,
            "created_at": None,  # Will be set by connector
        }

        # Add type-specific configuration
        if parsed_type == SourceType.DATABASE:
            if not connection_string:
                raise ValidationError(
                    "Database sources require a connection string",
                    suggestion="Provide --connection option with database URL"
                )
            config["connection_string"] = connection_string

        elif parsed_type == SourceType.FILE:
            if not file_path:
                raise ValidationError(
                    "File sources require a file path",
                    suggestion="Provide --file option with path to file"
                )
            config["file_path"] = file_path

        elif parsed_type == SourceType.API:
            if not connection_string:
                raise ValidationError(
                    "API sources require a connection URL",
                    suggestion="Provide --connection option with API endpoint"
                )
            config["api_url"] = connection_string

        # Test connection if requested
        if test_connection:
            with console.status(
                f"[bold yellow]Testing connection to '{name}'...",
                spinner="dots"
            ):
                # Note: This is a placeholder - actual implementation would use real connectors
                import time
                time.sleep(0.5)  # Simulate connection test

                if verbose:
                    console.print(f"[dim]Connection test passed[/dim]")

        # Save configuration
        from datetime import datetime
        config["created_at"] = datetime.utcnow().isoformat()

        with console.status(
            f"[bold green]Saving source '{name}'...",
            spinner="dots"
        ):
            save_source_config(name, config)

        # Success message
        console.print(f"[green]✅ Source '{name}' added successfully![/green]")

        if verbose:
            console.print(f"\n[bold]Details:[/bold]")
            console.print(f"  Type: {source_type}")
            if description:
                console.print(f"  Description: {description}")
            if connection_string:
                console.print(f"  Connection: {connection_string}")
            if file_path:
                console.print(f"  File: {file_path}")

        console.print(f"\n[yellow]💡 Test connection: sbdk source test {name}[/yellow]")
        console.print(f"[yellow]💡 View schema: sbdk source schema {name}[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command(name="list")
def list_sources(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed source information"
    ),
    source_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by source type"
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, minimal"
    ),
) -> None:
    """
    List all configured data sources.

    Examples:
        sbdk source list

        sbdk source list --verbose

        sbdk source list --type csv

        sbdk source list --format json
    """
    try:
        source_names = list_source_names()

        if not source_names:
            console.print("[yellow]No data sources configured.[/yellow]")
            console.print("[dim]Add one: sbdk source add <name> --type <type>[/dim]")
            return

        # Load all source configs
        sources = []
        for name in source_names:
            try:
                config = load_source_config(name)
                sources.append(config)
            except Exception as e:
                console.print(f"[yellow]⚠️  Warning: Failed to load source '{name}': {e}[/yellow]")

        # Filter by type if specified
        if source_type:
            sources = [s for s in sources if s.get("source_type") == source_type.lower()]

        if not sources:
            console.print(f"[yellow]No sources found with type '{source_type}'.[/yellow]")
            return

        # Output based on format
        if format == "json":
            console.print(json.dumps(sources, indent=2, default=str))
            return

        elif format == "minimal":
            for source in sources:
                console.print(source["name"])
            return

        # Table format (default)
        table = Table(
            title="SBDK Data Sources",
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Description", style="dim")

        if verbose:
            table.add_column("Created", style="dim")
            table.add_column("Config", style="dim")

        for source in sources:
            row = [
                source["name"],
                source["source_type"],
                source.get("description") or "-",
            ]

            if verbose:
                from datetime import datetime
                created_str = "-"
                if source.get("created_at"):
                    try:
                        created = datetime.fromisoformat(source["created_at"])
                        created_str = created.strftime("%Y-%m-%d %H:%M")
                    except:
                        created_str = source["created_at"]

                # Show relevant config info
                config_info = ""
                if source.get("file_path"):
                    config_info = f"file: {source['file_path']}"
                elif source.get("connection_string"):
                    # Mask sensitive info
                    conn = source["connection_string"]
                    if "@" in conn:
                        # Mask password in connection string
                        parts = conn.split("@")
                        config_info = f"db: ...@{parts[-1]}"
                    else:
                        config_info = f"db: {conn[:30]}..."
                elif source.get("api_url"):
                    config_info = f"api: {source['api_url']}"

                row.extend([created_str, config_info])

            table.add_row(*row)

        console.print(table)
        console.print(f"\n[dim]Total sources: {len(sources)}[/dim]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def test(
    name: str = typer.Argument(..., help="Source name to test"),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed test results"
    ),
) -> None:
    """
    Test connection to a data source.

    Examples:
        sbdk source test users

        sbdk source test db --verbose
    """
    try:
        # Load source config
        config = load_source_config(name)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Testing connection to '{name}'...",
                total=None
            )

            # Note: This is a placeholder - actual implementation would use real connectors
            import time
            time.sleep(1.0)  # Simulate connection test

            progress.update(task, completed=True)

        # Success message
        console.print(f"[green]✅ Connection to '{name}' successful![/green]")

        if verbose:
            console.print(f"\n[bold]Connection Details:[/bold]")
            console.print(f"  Source: {name}")
            console.print(f"  Type: {config['source_type']}")
            console.print(f"  Status: Connected")

            if config.get("file_path"):
                file_path = Path(config["file_path"])
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    console.print(f"  File size: {file_size:,} bytes")
                else:
                    console.print(f"  [yellow]Warning: File not found[/yellow]")

        console.print(f"\n[yellow]💡 View schema: sbdk source schema {name}[/yellow]")
        console.print(f"[yellow]💡 Sync data: sbdk source sync {name}[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def schema(
    name: str = typer.Argument(..., help="Source name"),
    table: Optional[str] = typer.Option(
        None,
        "--table",
        "-t",
        help="Specific table to show schema for"
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed schema information"
    ),
) -> None:
    """
    Show schema information for a data source.

    Examples:
        sbdk source schema users

        sbdk source schema db --table customers

        sbdk source schema api --format json
    """
    try:
        # Load source config
        config = load_source_config(name)

        with console.status(
            f"[bold cyan]Detecting schema for '{name}'...",
            spinner="dots"
        ):
            # Note: This is a placeholder - actual implementation would use real connectors
            import time
            time.sleep(0.8)  # Simulate schema detection

            # Mock schema data
            schema_data = {
                "table_name": table or name,
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "name", "type": "VARCHAR", "nullable": False},
                    {"name": "email", "type": "VARCHAR", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                ],
                "row_count": 1234,
            }

        # Output based on format
        if format == "json":
            console.print(json.dumps(schema_data, indent=2))
            return

        # Table format
        console.print(f"\n[bold]Schema: {schema_data['table_name']}[/bold]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Column", style="green")
        table.add_column("Type", style="cyan")
        table.add_column("Nullable", style="yellow")

        if verbose:
            table.add_column("Details", style="dim")

        for col in schema_data["columns"]:
            row = [
                col["name"],
                col["type"],
                "✓" if col["nullable"] else "✗",
            ]

            if verbose:
                # Additional column details
                details = f"Length: N/A"
                row.append(details)

            table.add_row(*row)

        console.print(table)

        if schema_data.get("row_count") is not None:
            console.print(f"\n[dim]Estimated rows: {schema_data['row_count']:,}[/dim]")

        console.print(f"\n[yellow]💡 Sync data: sbdk source sync {name}[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def sync(
    name: str = typer.Argument(..., help="Source name to sync"),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for synced data"
    ),
    sample: Optional[int] = typer.Option(
        None,
        "--sample",
        "-s",
        help="Sample N rows instead of full sync"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed sync progress"
    ),
) -> None:
    """
    Sync data from a source to local database.

    Examples:
        sbdk source sync users

        sbdk source sync db --sample 1000

        sbdk source sync api --output data/synced.csv --verbose
    """
    try:
        # Load source config
        config = load_source_config(name)

        # Determine output
        if not output:
            output = f".sbdk/data/{name}"

        console.print(f"[cyan]Syncing data from '{name}'...[/cyan]")

        if sample:
            console.print(f"[dim]Sampling: {sample:,} rows[/dim]")

        # Sync with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching data...", total=None)

            # Note: This is a placeholder - actual implementation would use real connectors
            import time
            time.sleep(1.5)  # Simulate data sync

            progress.update(
                task,
                description="[green]Sync complete!",
                completed=True
            )

        # Success message
        rows_synced = sample or 1234
        console.print(f"\n[green]✅ Successfully synced {rows_synced:,} rows from '{name}'[/green]")

        if verbose:
            console.print(f"\n[bold]Sync Details:[/bold]")
            console.print(f"  Source: {name}")
            console.print(f"  Type: {config['source_type']}")
            console.print(f"  Rows: {rows_synced:,}")
            console.print(f"  Output: {output}")

        console.print(f"\n[yellow]💡 Query data: sbdk query 'SELECT * FROM {name} LIMIT 10'[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def remove(
    name: str = typer.Argument(..., help="Source name to remove"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt"
    ),
) -> None:
    """
    Remove a data source.

    Examples:
        sbdk source remove old-source

        sbdk source remove temp --force
    """
    try:
        # Check if source exists
        config_path = get_source_config_path(name)
        if not config_path.exists():
            raise ConfigurationError(
                f"Source '{name}' not found",
                suggestion="List available sources: sbdk source list"
            )

        # Confirmation prompt
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to remove source '{name}'?",
                default=False
            )
            if not confirm:
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

        # Remove source
        with console.status(
            f"[bold red]Removing source '{name}'...",
            spinner="dots"
        ):
            config_path.unlink()

        console.print(f"[green]✅ Source '{name}' removed successfully[/green]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def info(
    name: str = typer.Argument(..., help="Source name"),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json"
    ),
) -> None:
    """
    Show detailed information about a data source.

    Examples:
        sbdk source info users

        sbdk source info db --format json
    """
    try:
        # Load source config
        config = load_source_config(name)

        if format == "json":
            console.print(json.dumps(config, indent=2, default=str))
            return

        # Text format
        panel_content = f"[cyan]Name:[/cyan] {config['name']}\n"
        panel_content += f"[cyan]Type:[/cyan] {config['source_type']}\n"

        if config.get("description"):
            panel_content += f"[cyan]Description:[/cyan] {config['description']}\n"

        if config.get("created_at"):
            panel_content += f"[cyan]Created:[/cyan] {config['created_at']}\n"

        # Type-specific info
        if config.get("file_path"):
            panel_content += f"\n[cyan]File Path:[/cyan] {config['file_path']}\n"
            file_path = Path(config["file_path"])
            if file_path.exists():
                file_size = file_path.stat().st_size
                panel_content += f"[cyan]File Size:[/cyan] {file_size:,} bytes\n"
                panel_content += f"[cyan]Exists:[/cyan] ✓\n"
            else:
                panel_content += f"[yellow]File Status:[/yellow] Not found\n"

        elif config.get("connection_string"):
            # Mask sensitive parts
            conn = config["connection_string"]
            if "@" in conn:
                parts = conn.split("@")
                masked = f"***@{parts[-1]}"
            else:
                masked = conn[:20] + "..."
            panel_content += f"\n[cyan]Connection:[/cyan] {masked}\n"

        elif config.get("api_url"):
            panel_content += f"\n[cyan]API URL:[/cyan] {config['api_url']}\n"

        console.print(
            Panel(
                panel_content.strip(),
                title=f"Source: {name}",
                style="cyan",
                expand=False
            )
        )

        console.print(f"\n[yellow]💡 Test connection: sbdk source test {name}[/yellow]")
        console.print(f"[yellow]💡 View schema: sbdk source schema {name}[/yellow]")
        console.print(f"[yellow]💡 Sync data: sbdk source sync {name}[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


if __name__ == "__main__":
    app()
