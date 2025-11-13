"""
Watch Command for SBDK - Hot-Reload Development Mode

Provides `sbdk watch` command for automatic pipeline reloading during
development with rich console feedback and smart change detection.

This command enhances the development experience by:
- Automatically reloading pipelines on file changes
- Showing clear feedback about what changed and reloaded
- Debouncing rapid changes (500ms default)
- Supporting both pipelines and dbt transformations
"""

import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from sbdk.dev.reload import PipelineReloader, ReloadError
from sbdk.dev.watcher import FileWatcher, WatchConfig

console = Console()

# Create watch command app
cli_watch = typer.Typer(
    name="watch",
    help="Watch files and auto-reload pipeline on changes"
)


@cli_watch.command()
def watch(
    config: str = typer.Option(
        "sbdk_config.json",
        "--config",
        "-c",
        help="Config file path"
    ),
    pipelines_only: bool = typer.Option(
        False,
        "--pipelines-only",
        help="Run only pipelines, skip dbt"
    ),
    dbt_only: bool = typer.Option(
        False,
        "--dbt-only",
        help="Run only dbt, skip pipelines"
    ),
    debounce: float = typer.Option(
        0.5,
        "--debounce",
        "-d",
        help="Debounce time in seconds (default: 0.5s)"
    ),
    watch_path: str = typer.Option(
        ".",
        "--watch",
        "-w",
        help="Path to watch (default: current directory)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed change information"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output"
    ),
) -> None:
    """
    Watch for file changes and auto-reload pipeline.

    This command watches your project directories for changes to Python,
    SQL, and YAML files, then automatically reloads your pipeline when
    changes are detected. Perfect for rapid iteration during development.

    Examples:
        # Basic watch mode
        sbdk watch

        # Watch with verbose output
        sbdk watch --verbose

        # Only watch pipelines, skip dbt
        sbdk watch --pipelines-only

        # Custom debounce and watch path
        sbdk watch --debounce 1.0 --watch ./src

        # Quiet mode for scripting
        sbdk watch --quiet
    """
    try:
        # Validate configuration file
        if not Path(config).exists():
            console.print(
                f"[red]❌ Configuration file not found: {config}[/red]"
            )
            console.print(
                "[yellow]💡 Run 'sbdk init' to create a project configuration[/yellow]"
            )
            raise typer.Exit(1)

        # Validate watch path
        watch_dir = Path(watch_path)
        if not watch_dir.exists():
            console.print(
                f"[red]❌ Watch directory not found: {watch_path}[/red]"
            )
            raise typer.Exit(1)

        # Show initial header
        if not quiet:
            console.print(
                Panel(
                    "[cyan]🔄 Hot-Reload Development Mode[/cyan]\n\n"
                    "Watching for changes...\n"
                    f"[dim]Watch path: {watch_path}[/dim]\n"
                    f"[dim]Debounce: {debounce}s[/dim]\n\n"
                    "[yellow]Press Ctrl+C to exit[/yellow]",
                    title="SBDK Watch Mode",
                    style="cyan",
                    expand=False
                )
            )

        # Initialize reloader
        reloader = PipelineReloader(
            config_path=config,
            pipelines_only=pipelines_only,
            dbt_only=dbt_only,
            quiet=quiet,
            verbose=verbose,
            console=console
        )

        # Run initial reload
        if not quiet:
            console.print("[cyan]Running initial pipeline...[/cyan]")

        try:
            result = reloader.reload()
            if not result.is_success():
                if not quiet:
                    console.print(
                        "[yellow]⚠️  Initial reload failed, watching anyway...[/yellow]"
                    )
        except Exception as e:
            if not quiet:
                console.print(
                    f"[yellow]⚠️  Initial reload failed: {e}[/yellow]\n"
                    "[yellow]Continuing to watch for changes...[/yellow]"
                )

        # Configure watcher
        watch_config = WatchConfig(
            debounce_seconds=debounce,
            quiet=quiet,
            verbose=verbose
        )

        # Create watcher with reload callback
        watcher = FileWatcher(
            paths=watch_path,
            config=watch_config,
            callback=lambda: _reload_pipeline(reloader, quiet),
            console=console
        )

        # Start watching
        watcher.start()

        try:
            # Keep the watcher running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            watcher.stop()
            if not quiet:
                console.print(
                    "\n[yellow]👋 Stopped watching for changes[/yellow]"
                )
                console.print(
                    f"[dim]Total reloads: {reloader.get_execution_count()}[/dim]"
                )

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


def _reload_pipeline(reloader: PipelineReloader, quiet: bool) -> None:
    """
    Internal function to reload pipeline and handle errors.

    Args:
        reloader: PipelineReloader instance
        quiet: Suppress output
    """
    try:
        result = reloader.reload()
        if not result.is_success() and result.error and not quiet:
            console.print(f"[yellow]Error: {result.error}[/yellow]")
    except ReloadError as e:
        if not quiet:
            console.print(f"[yellow]Reload error: {e.message}[/yellow]")
    except Exception as e:
        if not quiet:
            console.print(f"[yellow]Unexpected error: {e}[/yellow]")


# Export the CLI app
__all__ = ["cli_watch", "watch"]
