"""
Debug commands for troubleshooting SBDK setup
"""

import json
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands.run import load_config
from .dbt_utils import DbtRunner, find_dbt_executable

console = Console()


def cli_debug(
    config_file: str = typer.Option("sbdk_config.json", help="Config file path"),
    dbt_only: bool = typer.Option(
        False, "--dbt-only", help="Debug only dbt configuration"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
):
    """Debug SBDK configuration and environment setup"""

    console.print(
        Panel(
            "[cyan]🔍 SBDK Debug Information[/cyan]", title="Debug Mode", style="cyan"
        )
    )

    # System Information
    if not dbt_only:
        console.print("\n[bold]System Information:[/bold]")
        sys_table = Table()
        sys_table.add_column("Property", style="cyan")
        sys_table.add_column("Value", style="green")

        sys_table.add_row("Python Version", sys.version.split()[0])
        sys_table.add_row("Python Executable", sys.executable)
        sys_table.add_row("Current Working Directory", str(Path.cwd()))
        sys_table.add_row(
            "Virtual Environment", os.environ.get("VIRTUAL_ENV", "Not active")
        )
        sys_table.add_row(
            "PATH",
            (
                os.environ.get("PATH", "")[:100] + "..."
                if len(os.environ.get("PATH", "")) > 100
                else os.environ.get("PATH", "")
            ),
        )

        console.print(sys_table)

    # Configuration Information
    if not dbt_only:
        console.print("\n[bold]Configuration:[/bold]")
        try:
            config = load_config(config_file)

            config_table = Table()
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="green")
            config_table.add_column("Status", style="yellow")

            for key, value in config.items():
                if isinstance(value, dict):
                    value = json.dumps(value, indent=2)

                # Check if paths exist
                status = "✅"
                if key in ["dbt_path", "profiles_dir", "duckdb_path"]:
                    path = Path(str(value))
                    if key == "duckdb_path":
                        # Check if parent directory exists for database files
                        status = (
                            "✅" if path.parent.exists() else "❌ Parent dir missing"
                        )
                    else:
                        status = "✅" if path.exists() else "❌ Not found"

                config_table.add_row(
                    key,
                    str(value)[:80] + "..." if len(str(value)) > 80 else str(value),
                    status,
                )

            console.print(config_table)

        except Exception as e:
            console.print(f"[red]Failed to load configuration: {e}[/red]")

    # dbt Information
    console.print("\n[bold]dbt Configuration:[/bold]")

    try:
        # Find dbt executable
        dbt_path = find_dbt_executable()
        console.print(f"[green]✅ dbt executable found:[/green] {dbt_path}")

        # Try to initialize dbt runner
        try:
            config = load_config(config_file)
            dbt_dir = Path(config["dbt_path"])
            profiles_dir = Path(config["profiles_dir"]).expanduser()

            runner = DbtRunner(project_dir=str(dbt_dir), profiles_dir=str(profiles_dir))

            console.print("[green]✅ dbt runner initialized successfully[/green]")

            # Run dbt debug
            console.print("\n[bold]dbt debug output:[/bold]")
            debug_info = runner.debug()

            if debug_info["exit_code"] == 0:
                console.print("[green]✅ dbt debug passed[/green]")
            else:
                console.print(
                    f"[red]❌ dbt debug failed (exit code: {debug_info['exit_code']})[/red]"
                )

            if verbose:
                console.print("\n[dim]dbt debug stdout:[/dim]")
                console.print(debug_info["stdout"] or "[dim]No stdout[/dim]")

                if debug_info["stderr"]:
                    console.print("\n[dim]dbt debug stderr:[/dim]")
                    console.print(debug_info["stderr"])

        except Exception as e:
            console.print(f"[red]❌ Failed to initialize dbt runner: {e}[/red]")

    except Exception as e:
        console.print(f"[red]❌ dbt executable not found: {e}[/red]")
        console.print("\n[yellow]Suggestions:[/yellow]")
        console.print("1. Install dbt: uv add dbt-duckdb")
        console.print("2. Or globally: uv tool install dbt-duckdb")
        console.print("3. Ensure your virtual environment is activated")

    # File System Check
    if not dbt_only:
        console.print("\n[bold]File System Check:[/bold]")

        try:
            config = load_config(config_file)

            paths_to_check = [
                ("dbt project", config.get("dbt_path")),
                ("dbt profiles", config.get("profiles_dir")),
                ("pipelines", config.get("pipelines_path", "./pipelines")),
                (
                    "data directory",
                    (
                        Path(config.get("duckdb_path", "")).parent
                        if config.get("duckdb_path")
                        else None
                    ),
                ),
            ]

            fs_table = Table()
            fs_table.add_column("Component", style="cyan")
            fs_table.add_column("Path", style="dim")
            fs_table.add_column("Status", style="green")

            for name, path in paths_to_check:
                if path is None:
                    continue

                path_obj = Path(path)
                if path_obj.exists():
                    if path_obj.is_dir():
                        file_count = (
                            len(list(path_obj.rglob("*"))) if path_obj.is_dir() else 0
                        )
                        status = f"✅ Directory ({file_count} files)"
                    else:
                        status = "✅ File exists"
                else:
                    status = "❌ Not found"

                fs_table.add_row(
                    name,
                    str(path)[:60] + "..." if len(str(path)) > 60 else str(path),
                    status,
                )

            console.print(fs_table)

        except Exception as e:
            console.print(f"[red]Failed to check file system: {e}[/red]")

    console.print("\n[bold green]Debug complete![/bold green]")

    if not dbt_only:
        console.print("\n[dim]💡 Tips:[/dim]")
        console.print("[dim]- Use --dbt-only to focus on dbt issues[/dim]")
        console.print("[dim]- Use --verbose to see full dbt debug output[/dim]")
        console.print(
            "[dim]- Run 'sbdk dev --pipelines-only' to test pipeline execution[/dim]"
        )
        console.print("[dim]- Run 'sbdk dev --dbt-only' to test dbt execution[/dim]")
