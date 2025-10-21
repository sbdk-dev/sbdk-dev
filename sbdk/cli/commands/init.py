"""
Project initialization commands
"""

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
    project_name: str = typer.Argument(
        "my_project", help="Name of the project to create"
    ),
    template: Optional[str] = typer.Option("default", help="Template to use"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing directory"
    ),
):
    """Initialize a new SBDK project with pipelines and dbt models"""

    project_path = Path(project_name)

    # Check if directory exists
    if project_path.exists() and not force:
        console.print(
            f"[red]Directory {project_name} already exists. Use --force to overwrite.[/red]"
        )
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

        # Copy query.py helper script
        query_script = templates_root / "query.py"
        if query_script.exists():
            shutil.copy2(query_script, project_path / "query.py")

        # Update dbt_project.yml with the correct project name
        dbt_project_path = project_path / "dbt" / "dbt_project.yml"
        if dbt_project_path.exists():
            with open(dbt_project_path) as f:
                content = f.read()

            # Replace template placeholders with actual project name
            content = content.replace("{project_name}", project_name)
            content = content.replace("sbdk_project", project_name)

            with open(dbt_project_path, "w") as f:
                f.write(content)

        # Create config file
        progress.add_task("Creating configuration...", total=None)
        config = {
            "project": project_name,
            "target": "dev",
            "duckdb_path": f"data/{project_name}.duckdb",
            "pipelines_path": "./pipelines",
            "dbt_path": "./dbt",
            "profiles_dir": "~/.dbt",
        }

        config_path = project_path / "sbdk_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Create data directory
        progress.add_task("Setting up data directory...", total=None)
        (project_path / "data").mkdir(exist_ok=True)

        # Create dbt profiles directory and configure local database
        progress.add_task("Configuring dbt profiles...", total=None)
        dbt_profiles_dir = Path.home() / ".dbt"
        dbt_profiles_dir.mkdir(exist_ok=True)

        # Use project-specific profile name with local database path
        profiles_content = f"""
{project_name}:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: data/{project_name}.duckdb
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

    console.print(
        Panel(
            f"[green]✅ Successfully initialized SBDK project: {project_name}[/green]\n\n"
            f"[cyan]Next steps:[/cyan]\n"
            f"1. cd {project_name}\n"
            f"2. uv run sbdk run                          # Execute pipeline\n"
            f"3. python query.py                          # Query your data\n"
            f"4. uv run sbdk run --visual                 # Run with visual interface\n\n"
            f"[cyan]Query your data:[/cyan]\n"
            f"• python query.py                           # Show all tables\n"
            f'• python query.py "SELECT * FROM users"     # Run SQL query\n'
            f"• python query.py --interactive             # Interactive mode\n\n"
            f"[yellow]✨ Ready to go! No virtual environment setup needed with uv.[/yellow]",
            title="🎉 Project Created",
            style="green",
        )
    )
