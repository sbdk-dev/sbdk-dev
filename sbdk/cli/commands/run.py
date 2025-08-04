"""
Pipeline execution commands
"""

import json
import os
import subprocess
import sys
import time
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
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

console = Console()


def load_config(config_path: str = "sbdk_config.json") -> dict:
    """Load SBDK configuration"""
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        console.print("[red]Config file not found. Run 'sbdk init' first.[/red]")
        raise typer.Exit(1) from None


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


def run_visual_interface(config: dict):
    """Start the interactive CLI interface"""
    try:
        from sbdk.cli.interactive import start_interactive

        console.print("[cyan]Starting interactive interface...[/cyan]")
        start_interactive(".")

    except ImportError as e:
        console.print(
            f"[yellow]Interactive interface not available: {e}[/yellow]"
        )
        console.print("[dim]Falling back to single run mode[/dim]")
        execute_pipeline(config)
    except Exception as e:
        console.print(f"[red]Interactive interface failed: {e}[/red]")
        console.print("[yellow]Falling back to single run mode[/yellow]")
        execute_pipeline(config)


def execute_pipeline(
    config: dict, pipelines_only: bool = False, dbt_only: bool = False
):
    """Execute the data pipeline"""

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
            # Run dbt transformations
            dbt_task = progress.add_task("Running dbt transformations...", total=2)

            # dbt run
            progress.update(dbt_task, description="Running dbt models...")
            try:
                dbt_dir = Path(config["dbt_path"])
                profiles_dir = os.path.expanduser(config["profiles_dir"])
                subprocess.run(
                    [
                        "dbt",
                        "run",
                        "--project-dir",
                        str(dbt_dir),
                        "--profiles-dir",
                        profiles_dir,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                progress.advance(dbt_task)

                # dbt test
                progress.update(dbt_task, description="Running dbt tests...")
                subprocess.run(
                    [
                        "dbt",
                        "test",
                        "--project-dir",
                        str(dbt_dir),
                        "--profiles-dir",
                        profiles_dir,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                progress.advance(dbt_task)

                progress.update(dbt_task, description="✅ dbt transformations complete")

            except subprocess.CalledProcessError as e:
                console.print(f"[red]dbt command failed: {e}[/red]")
                if e.stdout:
                    console.print(f"[yellow]STDOUT:[/yellow] {e.stdout}")
                if e.stderr:
                    console.print(f"[yellow]STDERR:[/yellow] {e.stderr}")
                raise typer.Exit(1) from e

    console.print(
        Panel(
            "[green]🎉 Pipeline execution completed successfully![/green]\n\n"
            f"[cyan]Data available in:[/cyan] {config['duckdb_path']}\n"
            f"[cyan]Query your data:[/cyan] duckdb {config['duckdb_path']}\n",
            title="✅ Pipeline Complete",
            style="green",
        )
    )


class PipelineFileHandler(FileSystemEventHandler):
    """Handler for file system events during development"""

    def __init__(
        self, config: dict = None, visual: bool = False, debounce_seconds: float = 2.0
    ):
        self.config = config or {}
        self.visual = visual
        self.last_run = 0
        self.last_triggered = 0  # For backward compatibility with tests
        self.debounce_seconds = debounce_seconds

    def on_modified(self, event):
        if event.is_directory:
            return

        # Only react to pipeline and dbt files
        if not (event.src_path.endswith((".py", ".sql", ".yml", ".yaml"))):
            return

        # Debounce rapid file changes
        current_time = time.time()
        if current_time - self.last_run < self.debounce_seconds:
            return

        self.last_run = current_time
        self.last_triggered = current_time  # For backward compatibility

        console.print(f"\n[yellow]File changed: {event.src_path}[/yellow]")
        console.print("[cyan]Re-running pipeline...[/cyan]")

        try:
            execute_pipeline(self.config)
        except Exception as e:
            console.print(f"[red]Pipeline execution failed: {e}[/red]")


# Alias for backward compatibility with tests
PipelineHandler = PipelineFileHandler


def cli_run(
    visual: bool = typer.Option(False, "--visual", help="Run with visual interface"),
    watch: bool = typer.Option(
        False, "--watch", help="Watch for file changes and auto-rerun"
    ),
    pipelines_only: bool = typer.Option(
        False, "--pipelines-only", help="Run only pipelines, skip dbt"
    ),
    dbt_only: bool = typer.Option(
        False, "--dbt-only", help="Run only dbt, skip pipelines"
    ),
    config_file: str = typer.Option(
        "sbdk_config.json", "--config", help="Config file path"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress non-essential output"
    ),
):
    """Execute data pipeline with DLT and dbt transformations"""

    config = load_config(config_file)

    if visual:
        # Run visual interface
        run_visual_interface(config)
        return

    if watch:
        # Development mode with file watching
        console.print(
            Panel(
                "[cyan]🔄 Development Mode[/cyan]\n\n"
                "Watching for file changes in:\n"
                f"• Pipelines: {config.get('pipelines_path', './pipelines')}\n"
                f"• dbt models: {config.get('dbt_path', './dbt')}\n\n"
                "[dim]Press Ctrl+C to stop[/dim]",
                title="Development Server",
                style="cyan",
            )
        )

        # Initial run
        console.print("[cyan]Running initial pipeline...[/cyan]")
        execute_pipeline(config, pipelines_only, dbt_only)

        # Set up file watcher
        event_handler = PipelineFileHandler(config, visual)
        observer = Observer()

        # Watch pipelines directory
        pipelines_path = config.get("pipelines_path", "./pipelines")
        if Path(pipelines_path).exists():
            observer.schedule(event_handler, pipelines_path, recursive=True)

        # Watch dbt directory
        dbt_path = config.get("dbt_path", "./dbt")
        if Path(dbt_path).exists():
            observer.schedule(event_handler, dbt_path, recursive=True)

        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            console.print("\n[yellow]Stopped development server[/yellow]")

        observer.join()
    else:
        # Single run
        if not quiet:
            console.print(
                Panel(
                    "[cyan]🚀 SBDK Pipeline Execution[/cyan]",
                    title="Starting Pipeline",
                    style="cyan",
                )
            )

        execute_pipeline(config, pipelines_only, dbt_only)
