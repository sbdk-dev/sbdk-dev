"""
Development server with file watching
"""
import time
import threading
from pathlib import Path
from typing import List
import typer
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cli.dev import cli_dev, load_config

console = Console()

class PipelineHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, debounce_seconds: float = 2.0):
        self.debounce_seconds = debounce_seconds
        self.last_triggered = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Debounce rapid file changes
        current_time = time.time()
        if current_time - self.last_triggered < self.debounce_seconds:
            return
            
        self.last_triggered = current_time
        
        # Check if it's a relevant file
        relevant_extensions = {'.py', '.sql', '.yml', '.yaml', '.json'}
        if Path(event.src_path).suffix.lower() in relevant_extensions:
            console.print(f"[yellow]📁 File changed: {event.src_path}[/yellow]")
            console.print("[cyan]🔄 Rebuilding pipeline...[/cyan]")
            
            try:
                # Run development pipeline
                cli_dev()
                console.print("[green]✅ Pipeline rebuilt successfully[/green]")
            except Exception as e:
                console.print(f"[red]❌ Pipeline rebuild failed: {e}[/red]")

def create_status_table() -> Table:
    """Create status table for live display"""
    table = Table(title="🚀 SBDK Development Server")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")
    
    table.add_row("File Watcher", "🟢 Active", "Monitoring for changes")
    table.add_row("DuckDB", "🟢 Ready", "Local database available")
    table.add_row("dbt", "🟢 Ready", "Transform models loaded")
    
    return table

def cli_start(
    watch_paths: List[str] = typer.Option(
        ["pipelines/", "dbt/models/"], 
        "--watch", 
        help="Paths to watch for changes"
    ),
    no_initial_run: bool = typer.Option(
        False, 
        "--no-initial-run",
        help="Skip initial pipeline run"
    )
):
    """Start development server with file watching and auto-rebuild"""
    
    config = load_config()
    
    # Initial pipeline run
    if not no_initial_run:
        console.print("[cyan]🚀 Running initial pipeline...[/cyan]")
        try:
            cli_dev()
        except:
            console.print("[yellow]⚠️  Initial pipeline failed, but continuing with watch mode[/yellow]")
    
    # Setup file watcher
    event_handler = PipelineHandler()
    observer = Observer()
    
    # Watch specified paths
    watched_paths = []
    for path_str in watch_paths:
        path = Path(path_str)
        if path.exists():
            observer.schedule(event_handler, str(path), recursive=True)
            watched_paths.append(str(path))
            console.print(f"[dim]👀 Watching: {path}[/dim]")
    
    if not watched_paths:
        console.print("[red]No valid paths to watch found![/red]")
        raise typer.Exit(1)
    
    observer.start()
    
    try:
        console.print(Panel(
            "[green]🎉 Development server started![/green]\n\n"
            f"[cyan]Watching paths:[/cyan] {', '.join(watched_paths)}\n"
            f"[cyan]Database:[/cyan] {config['duckdb_path']}\n\n"
            "[dim]Press Ctrl+C to stop[/dim]",
            title="🚀 SBDK Dev Server",
            style="green"
        ))
        
        # Keep the server running with status updates
        with Live(create_status_table(), refresh_per_second=1) as live:
            while True:
                time.sleep(1)
                live.update(create_status_table())
                
    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 Stopping development server...[/yellow]")
        observer.stop()
        
    observer.join()
    console.print("[green]✅ Development server stopped[/green]")