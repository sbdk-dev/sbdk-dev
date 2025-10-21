"""
Development mode command for SBDK - provides enhanced development experience
"""

import os
import time
from pathlib import Path
from typing import Optional

import typer
from dynaconf import Dynaconf
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Initialize console for rich output
console = Console()

# Create the dev command
cli_dev = typer.Typer(
    name="dev", help="Execute pipeline in development mode with hot reload"
)


class DevFileHandler(FileSystemEventHandler):
    """File system event handler for development mode"""

    def __init__(self, callback, debounce_seconds: float = 2.0):
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.last_triggered = 0

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return

        # Only watch Python, SQL, and YAML files
        if any(
            event.src_path.endswith(ext) for ext in [".py", ".sql", ".yml", ".yaml"]
        ):
            current_time = time.time()
            if current_time - self.last_triggered > self.debounce_seconds:
                self.last_triggered = current_time
                console.print(f"\n[yellow]🔄 File changed: {event.src_path}[/yellow]")
                self.callback()


def load_config(config_path: str = "sbdk_config.json") -> Optional[Dynaconf]:
    """Load SBDK configuration"""
    try:
        if not os.path.exists(config_path):
            console.print(f"[red]❌ Config file not found: {config_path}[/red]")
            console.print("[yellow]💡 Run 'sbdk init' to create a new project[/yellow]")
            raise typer.Exit(1)

        return Dynaconf(settings_files=[config_path], environments=False)
    except Exception as e:
        console.print(f"[red]❌ Failed to load config: {e}[/red]")
        raise typer.Exit(1) from None


def run_pipeline_module(module_path: Path, module_name: str) -> bool:
    """Run a single pipeline module"""
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            console.print(f"[green]✅ Executed {module_name} pipeline[/green]")
            return True
    except Exception as e:
        console.print(f"[red]❌ Error in {module_name}: {e}[/red]")
        return False
    return False


def execute_pipeline(
    config: Dynaconf,
    pipelines_only: bool = False,
    dbt_only: bool = False,
    quiet: bool = False,
):
    """Execute the pipeline with development feedback"""
    if not quiet:
        console.print(
            Panel.fit(
                "[bold blue]🚀 SBDK Development Mode[/bold blue]\n"
                f"[dim]Running in: {os.getcwd()}[/dim]",
                border_style="blue",
            )
        )

    # Execute pipelines
    if not dbt_only:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Running pipelines...", total=3)

            pipelines_dir = Path("pipelines")
            if pipelines_dir.exists():
                for pipeline in ["users", "events", "orders"]:
                    module_path = pipelines_dir / f"{pipeline}.py"
                    if module_path.exists():
                        run_pipeline_module(module_path, pipeline)
                        progress.advance(task)
                    else:
                        console.print(
                            f"[yellow]⚠️  Pipeline not found: {pipeline}.py[/yellow]"
                        )
            else:
                console.print("[yellow]⚠️  No pipelines directory found[/yellow]")

    # Execute dbt
    if not pipelines_only:
        import subprocess

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Running dbt...", total=2)

                # Run dbt deps
                subprocess.run(["dbt", "deps"], check=True, capture_output=True)
                progress.advance(task)

                # Run dbt run
                subprocess.run(
                    ["dbt", "run"], check=True, capture_output=True, text=True
                )
                progress.advance(task)

                if not quiet:
                    console.print("[green]✅ dbt execution completed[/green]")

        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ dbt execution failed: {e}[/red]")
            if e.stdout:
                console.print(f"[dim]{e.stdout}[/dim]")
        except FileNotFoundError:
            console.print(
                "[yellow]⚠️  dbt not found. Install with: pip install dbt-core dbt-duckdb[/yellow]"
            )


@cli_dev.command()
def dev(
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Watch for file changes and auto-rerun"
    ),
    pipelines_only: bool = typer.Option(
        False, "--pipelines-only", help="Run only pipelines, skip dbt"
    ),
    dbt_only: bool = typer.Option(
        False, "--dbt-only", help="Run only dbt, skip pipelines"
    ),
    config: str = typer.Option(
        "sbdk_config.json", "--config", "-c", help="Config file path"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress non-essential output"
    ),
):
    """
    🔧 Execute pipeline in development mode with enhanced feedback

    This command provides a development-focused experience with:
    - Enhanced error messages and debugging info
    - File watching with auto-reload
    - Progress indicators and status updates
    - Development-optimized performance
    """
    # Load configuration
    settings = load_config(config)

    # Initial run
    execute_pipeline(settings, pipelines_only, dbt_only, quiet)

    if watch:
        console.print("\n[bold yellow]👀 Watching for file changes...[/bold yellow]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        # Set up file watcher
        event_handler = DevFileHandler(
            lambda: execute_pipeline(settings, pipelines_only, dbt_only, quiet)
        )
        observer = Observer()
        observer.schedule(event_handler, path=".", recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            console.print("\n[yellow]👋 Stopping development server...[/yellow]")
        observer.join()

    console.print("\n[green]✨ Development session complete![/green]")


# Export the CLI
__all__ = ["cli_dev", "dev"]
