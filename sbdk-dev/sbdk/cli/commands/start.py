"""
Clean, simple development server with proper separation of concerns - V2
"""

import time
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional
import io
import sys
import contextlib

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from sbdk.cli.commands.dev import cli_dev, load_config

console = Console()


class LogCapture:
    """Capture pipeline output cleanly"""
    
    def __init__(self):
        self.buffer = io.StringIO()
        self.logs = []
        self.max_logs = 50
    
    @contextlib.contextmanager
    def capture(self):
        """Context manager to capture output"""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            sys.stdout = self.buffer
            sys.stderr = self.buffer
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Extract captured output
            output = self.buffer.getvalue()
            if output.strip():
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.logs.append(f"[{timestamp}] {output.strip()}")
                self.logs = self.logs[-self.max_logs:]  # Keep last 50 logs
            
            self.buffer = io.StringIO()  # Reset buffer
    
    def get_recent_logs(self, lines: int = 10) -> List[str]:
        """Get recent log lines"""
        return self.logs[-lines:]


class ServerState:
    """Clean state management"""
    
    def __init__(self):
        self.pipeline_running = False
        self.last_run_time = None
        self.last_run_success = None
        self.last_error = None
        self.total_runs = 0
        self.successful_runs = 0
        self.file_changes = []
        self.auto_run = True
        self.watching_paths = []
        self.log_capture = LogCapture()
        self.pending_manual_run = False
    
    def add_file_change(self, file_path: str):
        """Add a file change with timestamp"""
        change = {
            "file": Path(file_path).name,
            "path": file_path,
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": self._get_file_type(file_path)
        }
        self.file_changes.append(change)
        self.file_changes = self.file_changes[-10:]  # Keep last 10
    
    def _get_file_type(self, file_path: str) -> str:
        """Categorize file type"""
        path = Path(file_path)
        if "pipeline" in str(path):
            return "Pipeline"
        elif path.suffix == ".sql":
            return "dbt"
        elif path.suffix in [".yml", ".yaml"]:
            return "Config"
        else:
            return "Code"
    
    def start_pipeline_run(self):
        """Mark pipeline as starting"""
        self.pipeline_running = True
        self.total_runs += 1
        self.pending_manual_run = False
    
    def finish_pipeline_run(self, success: bool, error: str = None):
        """Mark pipeline as finished"""
        self.pipeline_running = False
        self.last_run_time = datetime.now().strftime("%H:%M:%S")
        self.last_run_success = success
        self.last_error = error
        if success:
            self.successful_runs += 1


class CleanFileHandler(FileSystemEventHandler):
    """Simple, clean file handler"""
    
    def __init__(self, state: ServerState, debounce_seconds: float = 3.0):
        self.state = state
        self.debounce_seconds = debounce_seconds
        self.last_triggered = 0
        self.pending_files = set()
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Filter relevant files
        relevant_extensions = {".py", ".sql", ".yml", ".yaml", ".json"}
        if Path(event.src_path).suffix.lower() not in relevant_extensions:
            return
            
        self.pending_files.add(event.src_path)
        
        # Debounce
        current_time = time.time()
        if current_time - self.last_triggered < self.debounce_seconds:
            return
            
        self.last_triggered = current_time
        self._process_changes()
    
    def _process_changes(self):
        """Process file changes"""
        if not self.pending_files:
            return
            
        # Add changes to state
        for file_path in self.pending_files:
            self.state.add_file_change(file_path)
        
        files_count = len(self.pending_files)
        self.pending_files.clear()
        
        # Show change notification  
        console.print(f"")  # Add spacing
        console.print(f"[yellow]📁 {files_count} file(s) changed[/yellow]")
        
        # Auto-run or show hint
        if self.state.auto_run and not self.state.pipeline_running:
            console.print("[cyan]🔄 Auto-running pipeline...[/cyan]")
            self._run_pipeline()
        elif not self.state.pipeline_running:
            self.state.pending_manual_run = True
            console.print("[dim]💡 Type 'r' to run pipeline, or 'a' to enable auto-run[/dim]")
    
    def run_pipeline_manual(self):
        """Run pipeline manually from command"""
        if self.state.pipeline_running:
            console.print("[yellow]⚠️  Pipeline already running - please wait[/yellow]")
            return False
            
        console.print("[cyan]🚀 Running pipeline manually...[/cyan]")
        self._run_pipeline()
        return True
    
    def _run_pipeline(self):
        """Run pipeline in background thread"""
        if self.state.pipeline_running:
            return
            
        thread = threading.Thread(target=self._run_pipeline_sync)
        thread.daemon = True
        thread.start()
    
    def _run_pipeline_sync(self):
        """Run pipeline synchronously"""
        self.state.start_pipeline_run()
        
        try:
            with self.state.log_capture.capture():
                cli_dev()
            
            self.state.finish_pipeline_run(True)
            console.print("[green]✅ Pipeline completed successfully[/green]")
            
        except Exception as e:
            error_msg = str(e)
            self.state.finish_pipeline_run(False, error_msg)
            console.print(f"[red]❌ Pipeline failed: {error_msg}[/red]")


def show_status(state: ServerState):
    """Show clean status display"""
    
    console.print("")  # Add spacing
    console.print("=" * 60)
    console.print("[bold green]🚀 SBDK Development Server Status[/bold green]")
    console.print("=" * 60)
    
    # Basic info
    uptime = datetime.now().strftime("%H:%M:%S")
    console.print(f"[cyan]Time:[/cyan] {uptime}")
    console.print(f"[cyan]Auto-run:[/cyan] {'ON' if state.auto_run else 'OFF'}")
    console.print(f"[cyan]Watching:[/cyan] {', '.join(state.watching_paths)}")
    
    # Pipeline status
    if state.pipeline_running:
        status = "🟡 Running"
    elif state.last_run_success is None:
        status = "⚪ Not run"
    elif state.last_run_success:
        status = "🟢 Success"
    else:
        status = "🔴 Failed"
        
    console.print(f"[cyan]Pipeline:[/cyan] {status}")
    
    if state.last_run_time:
        console.print(f"[cyan]Last run:[/cyan] {state.last_run_time}")
        
    if state.total_runs > 0:
        success_rate = (state.successful_runs / state.total_runs) * 100
        console.print(f"[cyan]Success rate:[/cyan] {state.successful_runs}/{state.total_runs} ({success_rate:.1f}%)")
    
    # Recent changes
    if state.file_changes:
        console.print("")
        console.print("[yellow]Recent changes:[/yellow]")
        for change in state.file_changes[-5:]:
            console.print(f"  [{change['time']}] {change['type']}: {change['file']}")
    
    # Pending actions
    if state.pending_manual_run:
        console.print("")
        console.print("[yellow]💡 Changes detected - type 'r' to run pipeline[/yellow]")
    
    # Last error
    if state.last_error:
        console.print("")
        console.print(f"[red]Last error:[/red] {state.last_error[:100]}...")
    
    console.print("=" * 60)


def show_logs(state: ServerState, lines: int = 20):
    """Show recent pipeline logs"""
    logs = state.log_capture.get_recent_logs(lines)
    
    console.print("")  # Add spacing
    
    if not logs:
        console.print("[dim]No recent logs available[/dim]")
        console.print("[dim]💡 Run a pipeline first with 'r' to see output[/dim]")
        return
    
    console.print(f"[bold cyan]Recent Pipeline Output (last {len(logs)} entries):[/bold cyan]")
    console.print("-" * 60)
    
    for log in logs:
        console.print(f"[dim]{log}[/dim]")
    
    console.print("-" * 60)


def show_help(state: ServerState = None):
    """Show available commands"""
    auto_status = "ON" if (state and state.auto_run) else "OFF"
    
    console.print("")  # Add spacing
    console.print("[bold cyan]🎮 SBDK Server Commands:[/bold cyan]")
    console.print("")
    console.print("[bold green]s[/bold green] - Show server status and recent activity")
    console.print("[bold green]r[/bold green] - Run pipeline manually (if not already running)")
    console.print(f"[bold green]a[/bold green] - Toggle auto-run mode (currently: {auto_status})")
    console.print("[bold green]l[/bold green] - Show recent pipeline logs and output")
    console.print("[bold green]c[/bold green] - Clear file change history")
    console.print("[bold green]h[/bold green] - Show this help menu")
    console.print("[bold red]q[/bold red] - Quit the development server")
    console.print("")
    console.print("[cyan]💡 Tips:[/cyan]")
    console.print("• When files change, they'll be detected automatically")
    console.print("• Auto-run mode will rebuild immediately on changes")
    console.print("• Manual mode lets you control when to rebuild")
    console.print("• All pipeline output is captured and viewable with 'l'")
    console.print("")
    console.print("[dim]Just type a letter and press Enter[/dim]")


def cli_start(
    watch_paths: list[str] = typer.Option(
        ["pipelines/", "dbt/models/"], "--watch", help="Paths to watch for changes"
    ),
    no_initial_run: bool = typer.Option(
        False, "--no-initial-run", help="Skip initial pipeline run"
    ),
):
    """Clean, simple development server"""
    
    # Handle typer options
    if hasattr(watch_paths, 'default'):
        watch_paths = watch_paths.default
    if hasattr(no_initial_run, 'default'):
        no_initial_run = no_initial_run.default
    
    # Initialize
    state = ServerState()
    config = load_config()
    
    console.print("[bold green]🚀 Starting SBDK Development Server[/bold green]")
    console.print(f"[cyan]Database:[/cyan] {config['duckdb_path']}")
    
    # Initial run
    if not no_initial_run:
        console.print("")
        console.print("[cyan]Running initial pipeline...[/cyan]")
        state.start_pipeline_run()
        
        try:
            with state.log_capture.capture():
                cli_dev()
            state.finish_pipeline_run(True)
            console.print("[green]✅ Initial pipeline completed successfully[/green]")
            
        except Exception as e:
            state.finish_pipeline_run(False, str(e))
            console.print(f"[red]❌ Initial pipeline failed: {e}[/red]")
            
            if not Confirm.ask("[yellow]Continue anyway?[/yellow]", default=True):
                raise typer.Exit(1)
    
    # Setup file watcher
    event_handler = CleanFileHandler(state)
    observer = Observer()
    
    watched_paths = []
    for path_str in watch_paths:
        path = Path(path_str)
        if path.exists():
            observer.schedule(event_handler, str(path), recursive=True)
            watched_paths.append(str(path))
            console.print(f"[dim]👀 Watching: {path}[/dim]")
    
    if not watched_paths:
        console.print("[red]❌ No valid paths to watch![/red]")
        raise typer.Exit(1)
    
    state.watching_paths = watched_paths
    observer.start()
    
    # Interactive loop
    console.print("")
    console.print("[green]✅ Server started![/green]")
    console.print("[dim]Type 'h' for help, 'q' to quit[/dim]")
    
    def handle_command(cmd: str) -> bool:
        """Handle a command and return whether to continue"""
        if cmd == 'q':
            return False
        elif cmd == 's':
            show_status(state)
        elif cmd == 'r':
            event_handler.run_pipeline_manual()
        elif cmd == 'a':
            state.auto_run = not state.auto_run
            status = "enabled" if state.auto_run else "disabled"
            console.print(f"[yellow]🔄 Auto-run {status}[/yellow]")
            if state.auto_run:
                console.print("[dim]💡 Pipeline will now run automatically when files change[/dim]")
                # Run immediately if there are pending changes
                if state.pending_manual_run:
                    console.print("[cyan]🔄 Running pipeline for pending changes...[/cyan]")
                    event_handler._run_pipeline()
            else:
                console.print("[dim]💡 Use 'r' to run pipeline manually when files change[/dim]")
        elif cmd == 'l':
            show_logs(state)
        elif cmd == 'c':
            state.file_changes.clear()
            state.pending_manual_run = False
            console.print("[green]🧹 Change history cleared[/green]")
        elif cmd == 'h':
            show_help(state)
        elif cmd == '':
            # Show brief status on empty input
            status = "🟡 Running" if state.pipeline_running else ("🟢 Ready" if state.last_run_success else "🔴 Failed")
            auto_status = "ON" if state.auto_run else "OFF"
            pending = " | Changes pending" if state.pending_manual_run else ""
            console.print(f"[dim]Status: {status} | Auto-run: {auto_status}{pending} | Type 'h' for help[/dim]")
        else:
            console.print(f"[red]❓ Unknown command: '{cmd}'[/red]")
            console.print("[dim]💡 Type 'h' to see available commands[/dim]")
        return True
    
    try:
        while True:
            try:
                command = Prompt.ask("[bold cyan]SBDK>[/bold cyan]", default="").lower().strip()
                if not handle_command(command):
                    break
                    
            except KeyboardInterrupt:
                console.print("")
                console.print("[yellow]💡 Use 'q' to quit gracefully[/yellow]")
            except EOFError:
                break
                
    finally:
        console.print("")
        console.print("[yellow]🛑 Shutting down server...[/yellow]")
        observer.stop()
        observer.join()
        console.print("[green]✅ Server stopped[/green]")


if __name__ == "__main__":
    cli_start()