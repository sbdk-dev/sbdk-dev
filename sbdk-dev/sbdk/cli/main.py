#!/usr/bin/env python3
"""
SBDK.dev CLI - Modern data pipeline sandbox toolkit
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from sbdk.cli.commands.init import cli_init
from sbdk.cli.commands.run import cli_run
from sbdk.cli.commands.webhooks import cli_webhooks
from sbdk.cli.debug import cli_debug

console = Console()
app = typer.Typer(
    name="sbdk",
    help="🚀 SBDK.dev - Local-first data pipeline sandbox",
    rich_markup_mode="rich",
)


@app.callback()
def main():
    """
    SBDK.dev - Build data pipelines with DLT, DuckDB, and dbt
    """
    pass


# Register CLI commands
app.command("init", help="🏗️ Initialize a new SBDK project")(cli_init)
app.command("run", help="🚀 Execute data pipeline")(cli_run)
app.command("webhooks", help="🔗 Start webhook listener server")(cli_webhooks)
app.command("debug", help="🔍 Debug SBDK configuration and environment")(cli_debug)


@app.command("version")
def version():
    """Show SBDK.dev version"""
    from sbdk import __version__

    console.print(
        Panel(
            Text(f"SBDK.dev v{__version__}", style="bold green"),
            title="Version",
            style="green",
        )
    )


if __name__ == "__main__":
    app()
