"""
SBDK Start Command Module
Provides CLI start functionality and pipeline handling
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console

from sbdk.core.config import SBDKConfig, load_config

console = Console()


class ServerStateEnum(Enum):
    """Server state enumeration"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ServerStateManager:
    """Manage server state and pipeline execution"""

    def __init__(self):
        self.state = ServerStateEnum.STOPPED
        self.pipeline_running = False
        self.total_runs = 0
        self.auto_run = True
        self.watching_paths = []
        self.file_changes = []
        self.last_run = None
        self.errors = []
        self.last_run_success = True
        self.successful_runs = 0
        self.last_error = None
        self.pending_manual_run = False
        self.log_capture = None

    def add_file_change(self, file_path: str):
        """Track file changes"""
        file_name = Path(file_path).name
        change_info = {
            "file": file_name,
            "type": "Pipeline" if file_path.endswith(".py") else "Config",
            "timestamp": datetime.now().isoformat(),
        }
        self.file_changes.append(change_info)

    def start_pipeline_run(self):
        """Start a pipeline run"""
        self.pipeline_running = True
        self.total_runs += 1
        self.last_run = datetime.now()

    def end_pipeline_run(self, success: bool = True):
        """End a pipeline run"""
        self.pipeline_running = False
        if not success:
            self.errors.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "error": "Pipeline run failed",
                }
            )

    def finish_pipeline_run(self, success: bool, error: str = None):
        """Finish a pipeline run with status"""
        self.pipeline_running = False
        self.last_run_success = success
        if success:
            self.successful_runs += 1
        else:
            self.last_error = error

    def get_status(self) -> dict:
        """Get current status"""
        return {
            "state": self.state.value,
            "pipeline_running": self.pipeline_running,
            "total_runs": self.total_runs,
            "auto_run": self.auto_run,
            "file_changes": len(self.file_changes),
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }


# Create a singleton instance for backward compatibility
ServerState = ServerStateManager


def cli_start(
    config_path: str = typer.Option("sbdk_config.json", help="Path to config file"),
    target: str = typer.Option("dev", help="Target environment"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Start SBDK pipeline processing"""
    try:
        config = load_config(config_path)
        console.print(f"[green]Starting SBDK with config: {config_path}[/green]")

        if verbose:
            console.print(f"Target: {target}")
            console.print(f"DuckDB Path: {config.duckdb_path}")
            console.print(f"Pipelines Path: {config.pipelines_path}")

        # Initialize pipeline handler
        handler = PipelineHandler(config)
        handler.start()

    except Exception as e:
        console.print(f"[red]Error starting SBDK: {e}[/red]")
        raise typer.Exit(1)


class PipelineHandler:
    """Handle pipeline execution and management"""

    def __init__(self, config: SBDKConfig):
        self.config = config
        self.console = Console()
        self.state = ServerStateEnum.STOPPED
        self.pipelines = []

    def start(self) -> None:
        """Start pipeline processing"""
        self.state = ServerStateEnum.STARTING
        self.console.print("[blue]Initializing pipeline handler...[/blue]")

        # Validate configuration
        validation_results = self.config.validate_paths()
        if not all(validation_results.values()):
            self.console.print("[yellow]Warning: Some paths are missing[/yellow]")
            for path, exists in validation_results.items():
                status = "✓" if exists else "✗"
                self.console.print(f"  {status} {path}")

        self.state = ServerStateEnum.RUNNING
        self.console.print("[green]Pipeline handler started successfully[/green]")

    def stop(self) -> None:
        """Stop pipeline processing"""
        self.state = ServerStateEnum.STOPPING
        self.console.print("[blue]Stopping pipeline handler...[/blue]")
        self.state = ServerStateEnum.STOPPED

    def status(self) -> dict:
        """Get pipeline status"""
        return {
            "status": self.state.value,
            "config": self.config.model_dump(),
            "timestamp": None,
            "pipelines": self.pipelines,
        }

    def add_pipeline(self, pipeline_name: str) -> None:
        """Add a pipeline to the handler"""
        self.pipelines.append(pipeline_name)

    def get_state(self) -> ServerStateEnum:
        """Get current server state"""
        return self.state


class CleanFileHandler:
    """Handle file operations with cleanup"""

    def __init__(self, state: ServerStateManager):
        self.state = state
        self.console = Console()
        self.handlers = []

    def cleanup_temp_files(self) -> None:
        """Clean up temporary files"""
        self.console.print("[blue]Cleaning up temporary files...[/blue]")

    def backup_files(self, paths: list) -> None:
        """Backup important files"""
        self.console.print(f"[blue]Backing up {len(paths)} files...[/blue]")

    def restore_files(self, backup_path: str) -> None:
        """Restore files from backup"""
        self.console.print(f"[blue]Restoring from backup: {backup_path}[/blue]")

    def add_handler(self, handler, path):
        """Add a file handler"""
        self.handlers.append((handler, path))

    def trigger_event(self, event_type: str, file_path: str):
        """Trigger a file system event"""
        for handler, watched_path in self.handlers:
            if file_path.startswith(str(watched_path)):
                # Create mock event
                event = type(
                    "Event",
                    (),
                    {
                        "src_path": file_path,
                        "event_type": event_type,
                        "is_directory": False,
                    },
                )()

                if event_type == "modified":
                    handler.on_modified(event)
                elif event_type == "created":
                    handler.on_created(event)

    def run_pipeline_manual(self) -> bool:
        """Run pipeline manually"""
        if self.state.pipeline_running:
            self.console.print("[yellow]Pipeline already running![/yellow]")
            return False

        self.console.print("[blue]Starting manual pipeline run...[/blue]")
        self.state.start_pipeline_run()
        # Simulate pipeline execution
        import time

        time.sleep(0.1)
        self.state.finish_pipeline_run(True)
        self.console.print("[green]Manual pipeline run completed[/green]")
        return True


class PipelineFileHandler:
    """Handle pipeline file events"""

    def __init__(self, state: ServerStateManager):
        self.state = state
        self.console = Console()

    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory:
            self.state.add_file_change(event.src_path)
            self.console.print(f"[yellow]File modified: {event.src_path}[/yellow]")

            if self.state.auto_run and not self.state.pipeline_running:
                self.run_pipelines()

    def on_created(self, event):
        """Handle file creation"""
        if not event.is_directory:
            self.state.add_file_change(event.src_path)
            self.console.print(f"[green]File created: {event.src_path}[/green]")

    def run_pipelines(self):
        """Execute pipelines"""
        self.state.start_pipeline_run()
        self.console.print("[blue]Running pipelines...[/blue]")
        # Simulate pipeline execution
        import time

        time.sleep(0.1)
        self.state.end_pipeline_run(success=True)
        self.console.print("[green]Pipelines completed successfully[/green]")


def cli_dev(
    config_path: str = typer.Option("sbdk_config.json", help="Path to config file"),
    port: int = typer.Option(8000, help="Development server port"),
    auto_reload: bool = typer.Option(True, help="Enable auto-reload"),
) -> None:
    """Start SBDK development server"""
    try:
        config = load_config(config_path)
        console.print(f"[green]Starting SBDK dev server on port {port}[/green]")

        if auto_reload:
            console.print("[blue]Auto-reload enabled[/blue]")

        # Start development server
        handler = PipelineHandler(config)
        handler.start()

    except Exception as e:
        console.print(f"[red]Error starting dev server: {e}[/red]")
        raise typer.Exit(1)
