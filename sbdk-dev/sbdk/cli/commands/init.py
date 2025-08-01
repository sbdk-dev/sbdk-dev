"""
Project initialization commands
"""
import os
import json
import shutil
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def cli_init(
    project_name: str = typer.Argument("my_project", help="Name of the project to create"),
    template: Optional[str] = typer.Option("default", help="Template to use"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing directory")
):
    """Initialize a new SBDK project with pipelines and dbt models"""
    
    project_path = Path(project_name)
    
    # Check if directory exists
    if project_path.exists() and not force:
        console.print(f"[red]Directory {project_name} already exists. Use --force to overwrite.[/red]")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Create project directory
        progress.add_task("Creating project directory...", total=None)
        project_path.mkdir(exist_ok=True)
        
        # Copy template files
        progress.add_task("Copying template files...", total=None)
        template_dirs = ["pipelines", "dbt", "fastapi_server"]
        
        # Find the templates directory in the installed package
        import sbdk
        package_root = Path(sbdk.__file__).parent
        templates_root = package_root / "templates"
        
        for dir_name in template_dirs:
            src_dir = templates_root / dir_name
            dst_dir = project_path / dir_name
            if src_dir.exists():
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        
        # Create config file
        progress.add_task("Creating configuration...", total=None)
        config = {
            "project": project_name,
            "target": "dev", 
            "duckdb_path": f"data/{project_name}.duckdb",
            "pipelines_path": "./pipelines",
            "dbt_path": "./dbt",
            "profiles_dir": "~/.dbt"
        }
        
        config_path = project_path / "sbdk_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        # Create data directory
        progress.add_task("Setting up data directory...", total=None)
        (project_path / "data").mkdir(exist_ok=True)
        
        # Create dbt profiles directory
        progress.add_task("Configuring dbt profiles...", total=None)
        dbt_profiles_dir = Path.home() / ".dbt"
        dbt_profiles_dir.mkdir(exist_ok=True)
        
        profiles_content = f"""
{project_name}:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: {project_path.absolute()}/data/{project_name}.duckdb
      schema: main
"""
        
        profiles_path = dbt_profiles_dir / "profiles.yml"
        if not profiles_path.exists():
            with open(profiles_path, "w") as f:
                f.write(profiles_content)
        else:
            # Append to existing profiles
            with open(profiles_path, "a") as f:
                f.write(profiles_content)
    
    console.print(Panel(
        f"[green]✅ Successfully initialized SBDK project: {project_name}[/green]\n\n"
        f"[cyan]Next steps:[/cyan]\n"
        f"1. cd {project_name}\n"
        f"2. python -m venv .venv\n"
        f"3. source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate\n"
        f"4. pip install sbdk-dev\n"
        f"5. sbdk dev\n",
        title="🎉 Project Created",
        style="green"
    ))