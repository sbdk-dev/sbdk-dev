"""
Development mode commands
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

def load_config(config_path: str = "sbdk_config.json") -> dict:
    """Load SBDK configuration"""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        console.print("[red]Config file not found. Run 'sbdk init' first.[/red]")
        raise typer.Exit(1)

def run_pipeline_module(module_name: str):
    """Run a specific pipeline module"""
    try:
        module_path = f"pipelines.{module_name}"
        result = subprocess.run([
            sys.executable, "-c", f"from {module_path} import run; run()"
        ], capture_output=True, text=True, check=True)
        
        if result.stdout:
            console.print(f"[dim]{result.stdout}[/dim]")
            
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Pipeline {module_name} failed: {e.stderr}[/red]")
        raise typer.Exit(1)

def cli_dev(
    pipelines_only: bool = typer.Option(False, "--pipelines-only", help="Run only pipelines, skip dbt"),
    dbt_only: bool = typer.Option(False, "--dbt-only", help="Run only dbt, skip pipelines"),
    config_file: str = typer.Option("sbdk_config.json", help="Config file path")
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
            for i, module in enumerate(pipeline_modules):
                progress.update(pipelines_task, description=f"Running {module} pipeline...")
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
                subprocess.run([
                    "dbt", "run", 
                    "--project-dir", str(dbt_dir),
                    "--profiles-dir", config["profiles_dir"]
                ], check=True, capture_output=True)
                progress.advance(dbt_task)
                
                # dbt test
                progress.update(dbt_task, description="Running dbt tests...")
                subprocess.run([
                    "dbt", "test",
                    "--project-dir", str(dbt_dir), 
                    "--profiles-dir", config["profiles_dir"]
                ], check=True, capture_output=True)
                progress.advance(dbt_task)
                
                progress.update(dbt_task, description="✅ dbt transformations complete")
                
            except subprocess.CalledProcessError as e:
                console.print(f"[red]dbt command failed: {e}[/red]")
                raise typer.Exit(1)
    
    console.print(Panel(
        "[green]🎉 Development pipeline completed successfully![/green]\n\n"
        f"[cyan]Data available in:[/cyan] {config['duckdb_path']}\n"
        f"[cyan]Query your data:[/cyan] duckdb {config['duckdb_path']}\n",
        title="✅ Pipeline Complete",
        style="green"
    ))