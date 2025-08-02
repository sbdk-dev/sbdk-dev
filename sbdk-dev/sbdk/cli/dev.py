"""
Development mode commands with robust dbt execution
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from .dbt_utils import DbtRunner

console = Console()


def load_config(config_path: str = "sbdk_config.json") -> dict:
    """Load SBDK configuration with enhanced path resolution"""
    try:
        # Try current directory first
        if not Path(config_path).exists():
            # Try common locations for sbdk-starter projects
            potential_paths = [
                Path.cwd() / config_path,
                Path.cwd().parent / config_path,
                Path(__file__).parent.parent / config_path,
            ]

            for path in potential_paths:
                if path.exists():
                    config_path = str(path)
                    break
            else:
                console.print(
                    "[red]Config file not found. Run 'sbdk init' first.[/red]"
                )
                console.print(
                    f"[dim]Searched paths: {[str(p) for p in potential_paths]}[/dim]"
                )
                raise typer.Exit(1)

        with open(config_path) as f:
            config = json.load(f)

        # Expand paths in configuration
        if "dbt_path" in config:
            config["dbt_path"] = str(Path(config["dbt_path"]).expanduser().resolve())
        if "profiles_dir" in config:
            config["profiles_dir"] = str(
                Path(config["profiles_dir"]).expanduser().resolve()
            )
        if "duckdb_path" in config:
            # Make duckdb_path relative to config file location if not absolute
            duckdb_path = Path(config["duckdb_path"])
            if not duckdb_path.is_absolute():
                config_dir = Path(config_path).parent
                config["duckdb_path"] = str((config_dir / duckdb_path).resolve())

        return config

    except FileNotFoundError:
        console.print("[red]Config file not found. Run 'sbdk init' first.[/red]")
        raise typer.Exit(1) from None
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in config file: {e}[/red]")
        raise typer.Exit(1) from e


def run_pipeline_module(module_name: str):
    """Run a specific pipeline module"""
    try:
        module_path = f"pipelines.{module_name}"
        result = subprocess.run(
            [sys.executable, "-c", f"from {module_path} import run; run()"],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout:
            console.print(f"[dim]{result.stdout}[/dim]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Pipeline {module_name} failed: {e.stderr}[/red]")
        raise typer.Exit(1) from e


def cli_dev(
    pipelines_only: bool = typer.Option(
        False, "--pipelines-only", help="Run only pipelines, skip dbt"
    ),
    dbt_only: bool = typer.Option(
        False, "--dbt-only", help="Run only dbt, skip pipelines"
    ),
    config_file: str = typer.Option("sbdk_config.json", help="Config file path"),
):
    """Run development pipeline: extract data, load to DuckDB, transform with dbt"""

    config = load_config(config_file)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        if not dbt_only:
            # Run data pipelines
            pipelines_task = progress.add_task("Running data pipelines...", total=3)

            pipeline_modules = ["users", "events", "orders"]
            for _i, module in enumerate(pipeline_modules):
                progress.update(
                    pipelines_task, description=f"Running {module} pipeline..."
                )
                run_pipeline_module(module)
                progress.advance(pipelines_task)

            progress.update(pipelines_task, description="✅ Pipelines complete")

        if not pipelines_only:
            # Run dbt transformations using robust runner
            dbt_task = progress.add_task("Running dbt transformations...", total=3)

            try:
                # Initialize robust dbt runner
                dbt_dir = Path(config["dbt_path"])
                profiles_dir = os.path.expanduser(config["profiles_dir"])

                progress.update(dbt_task, description="Initializing dbt runner...")
                runner = DbtRunner(project_dir=str(dbt_dir), profiles_dir=profiles_dir)
                progress.advance(dbt_task)

                # dbt run
                progress.update(dbt_task, description="Running dbt models...")
                runner.run(
                    debug=False
                )  # Disable debug output for cleaner progress display
                progress.advance(dbt_task)

                # dbt test
                progress.update(dbt_task, description="Running dbt tests...")
                runner.test(
                    debug=False
                )  # Disable debug output for cleaner progress display
                progress.advance(dbt_task)

                progress.update(dbt_task, description="✅ dbt transformations complete")

            except Exception as e:
                console.print(f"[red]dbt execution failed: {e}[/red]")

                # Try to provide helpful debug information
                try:
                    console.print("[yellow]Debugging dbt setup...[/yellow]")
                    debug_info = runner.debug() if "runner" in locals() else None
                    if debug_info:
                        console.print(
                            f"[dim]dbt executable: {debug_info['dbt_path']}[/dim]"
                        )
                        console.print(
                            f"[dim]Project directory: {debug_info['project_dir']}[/dim]"
                        )
                        console.print(
                            f"[dim]Profiles directory: {debug_info['profiles_dir']}[/dim]"
                        )
                except Exception:
                    console.print(
                        "[yellow]Could not retrieve debug information[/yellow]"
                    )

                raise typer.Exit(1) from e

    console.print(
        Panel(
            "[green]🎉 Development pipeline completed successfully![/green]\n\n"
            f"[cyan]Data available in:[/cyan] {config['duckdb_path']}\n"
            f"[cyan]Query your data:[/cyan] duckdb {config['duckdb_path']}\n",
            title="✅ Pipeline Complete",
            style="green",
        )
    )
