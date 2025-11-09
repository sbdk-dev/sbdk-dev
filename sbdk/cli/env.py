"""
Environment Management CLI Commands

Commands for creating, switching, and managing SBDK environments.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sbdk.environment import (
    EnvironmentManager,
    EnvironmentSwitcher,
    EnvironmentTarget,
    EnvironmentTemplate,
)
from sbdk.exceptions import SBDKError

app = typer.Typer(help="Environment management commands")
console = Console()


@app.command()
def create(
    name: str = typer.Argument(..., help="Environment name"),
    template: str = typer.Option(
        "basic",
        "--template",
        "-t",
        help="Template: analytics, ml, or basic"
    ),
    target: str = typer.Option(
        "duckdb",
        "--target",
        help="Target database: duckdb, postgres, bigquery, snowflake"
    ),
    copy_from: Optional[str] = typer.Option(
        None,
        "--copy-from",
        help="Copy settings from existing environment"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Environment description"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output"
    ),
) -> None:
    """
    Create a new SBDK environment.

    Examples:
        sbdk env create dev --template analytics

        sbdk env create staging --copy-from dev

        sbdk env create prod --template analytics --description "Production environment"
    """
    try:
        # Parse template
        try:
            env_template = EnvironmentTemplate(template.lower())
        except ValueError:
            console.print(
                f"[red]❌ Invalid template: {template}[/red]",
                style="red"
            )
            console.print(
                "[yellow]💡 Available templates: analytics, ml, basic[/yellow]"
            )
            raise typer.Exit(4)

        # Parse target
        try:
            env_target = EnvironmentTarget(target.lower())
        except ValueError:
            console.print(
                f"[red]❌ Invalid target: {target}[/red]",
                style="red"
            )
            console.print(
                "[yellow]💡 Available targets: duckdb, postgres, bigquery, snowflake[/yellow]"
            )
            raise typer.Exit(4)

        # Create manager
        manager = EnvironmentManager()

        # Create environment
        with console.status(f"[bold green]Creating environment '{name}'...", spinner="dots"):
            kwargs = {}
            if description:
                kwargs["description"] = description

            env_path = manager.create(
                name=name,
                template=env_template,
                target=env_target,
                copy_from=copy_from,
                **kwargs
            )

        # Success message
        console.print(f"[green]✅ Environment '{name}' created successfully![/green]")
        console.print(f"[dim]Location: {env_path}[/dim]")

        if verbose:
            console.print(f"\n[bold]Details:[/bold]")
            console.print(f"  Template: {template}")
            console.print(f"  Target: {target}")
            if copy_from:
                console.print(f"  Copied from: {copy_from}")
            if description:
                console.print(f"  Description: {description}")

        console.print(f"\n[yellow]💡 Switch to this environment: sbdk env switch {name}[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def switch(
    name: str = typer.Argument(..., help="Environment name to switch to"),
    fast: bool = typer.Option(
        False,
        "--fast",
        help="Skip validation for faster switching"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed timing information"
    ),
) -> None:
    """
    Switch to a different environment.

    Examples:
        sbdk env switch dev

        sbdk env switch prod --fast

        sbdk env switch staging --verbose
    """
    try:
        switcher = EnvironmentSwitcher()

        with console.status(f"[bold green]Switching to '{name}'...", spinner="dots"):
            if verbose:
                result = switcher.switch_with_validation(name)
            else:
                elapsed = switcher.switch(name, validate=not fast)
                result = {"elapsed": elapsed}

        # Success message
        console.print(f"[green]✅ Switched to environment '{name}'[/green]")

        if verbose:
            console.print(f"\n[bold]Performance:[/bold]")
            console.print(f"  Total time: {result['elapsed']:.3f}s")
            if "validation_time" in result:
                console.print(f"  Validation: {result['validation_time']:.3f}s")
                console.print(f"  Switch: {result['switch_time']:.3f}s")

            target_met = result.get("performance_target_met", result["elapsed"] < 2.0)
            if target_met:
                console.print(f"  [green]✅ Performance target met (<2s)[/green]")
            else:
                console.print(f"  [yellow]⚠️  Slower than target (>2s)[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command(name="list")
def list_environments(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed environment information"
    ),
) -> None:
    """
    List all SBDK environments.

    Examples:
        sbdk env list

        sbdk env list --verbose
    """
    try:
        manager = EnvironmentManager()
        environments = manager.list_environments()

        if not environments:
            console.print("[yellow]No environments found.[/yellow]")
            console.print("[dim]Create one: sbdk env create <name>[/dim]")
            return

        # Create table
        table = Table(title="SBDK Environments", show_header=True, header_style="bold magenta")

        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Active", justify="center")
        table.add_column("Template", style="green")
        table.add_column("Target", style="blue")

        if verbose:
            table.add_column("Created", style="dim")
            table.add_column("Description", style="dim")

        for env in environments:
            row = [
                env["name"],
                "✅" if env["is_active"] else "",
                env["template"],
                env["target"],
            ]

            if verbose:
                from datetime import datetime
                created = datetime.fromisoformat(env["created_at"])
                row.extend([
                    created.strftime("%Y-%m-%d %H:%M"),
                    env.get("description") or "-"
                ])

            table.add_row(*row)

        console.print(table)

        # Show summary
        active_env = manager.get_active_environment()
        if active_env:
            console.print(f"\n[green]Current environment: {active_env}[/green]")
        else:
            console.print(f"\n[yellow]No active environment[/yellow]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def status(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed status information"
    ),
) -> None:
    """
    Show current environment status.

    Examples:
        sbdk env status

        sbdk env status --verbose
    """
    try:
        manager = EnvironmentManager()
        status = manager.get_status()

        # Active environment
        if status["active_environment"]:
            console.print(f"[green]✅ Active Environment: {status['active_environment']}[/green]")

            if "active_config" in status:
                config = status["active_config"]
                console.print(f"\n[bold]Configuration:[/bold]")
                console.print(f"  Template: {config['template']}")
                console.print(f"  Target: {config['target']}")
                if config.get("description"):
                    console.print(f"  Description: {config['description']}")
        else:
            console.print("[yellow]⚠️  No active environment[/yellow]")
            console.print("[dim]Switch to one: sbdk env switch <name>[/dim]")

        # Environment summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total environments: {status['total_environments']}")
        console.print(f"  Environments directory: {status['environments_dir']}")

        if verbose:
            console.print(f"  SBDK home: {status['sbdk_home']}")

            # List all environments
            if status["environments"]:
                console.print(f"\n[bold]All environments:[/bold]")
                for env in status["environments"]:
                    icon = "→" if env["is_active"] else " "
                    console.print(f"  {icon} {env['name']} ({env['template']})")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def delete(
    name: str = typer.Argument(..., help="Environment name to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt"
    ),
) -> None:
    """
    Delete an environment.

    Examples:
        sbdk env delete old-env

        sbdk env delete staging --force
    """
    try:
        manager = EnvironmentManager()

        # Confirmation prompt
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete environment '{name}'?",
                default=False
            )
            if not confirm:
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

        # Delete environment
        with console.status(f"[bold red]Deleting environment '{name}'...", spinner="dots"):
            manager.delete(name, force=force)

        console.print(f"[green]✅ Environment '{name}' deleted successfully[/green]")

    except SBDKError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        if e.suggestion:
            console.print(f"[yellow]💡 {e.suggestion}[/yellow]")
        raise typer.Exit(e.exit_code)


@app.command()
def templates() -> None:
    """
    List available environment templates.

    Examples:
        sbdk env templates
    """
    from sbdk.environment import TemplateEngine

    engine = TemplateEngine()
    available_templates = engine.list_available_templates()

    console.print("[bold]Available Templates:[/bold]\n")

    for template_name, template_info in available_templates.items():
        console.print(f"[cyan]■ {template_name}[/cyan]")
        console.print(f"  {template_info['description']}")
        console.print(f"  Features: {', '.join(template_info['features'])}")
        console.print(f"  Use cases: {', '.join(template_info['use_cases'])}")
        console.print()

    console.print("[dim]Create environment: sbdk env create <name> --template <template>[/dim]")


if __name__ == "__main__":
    app()
