#!/usr/bin/env python3
"""
SBDK.dev CLI - Modern data pipeline sandbox toolkit
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from cli.init import cli_init
from cli.dev import cli_dev
from cli.start import cli_start
from cli.webhooks import cli_webhooks

console = Console()
app = typer.Typer(
    name="sbdk",
    help="🚀 SBDK.dev - Local-first data pipeline sandbox",
    rich_markup_mode="rich"
)

@app.callback()
def main():
    """
    SBDK.dev - Build data pipelines with DLT, DuckDB, and dbt
    """
    pass

# Register CLI commands
app.command("init", help="🏗️  Initialize a new SBDK project")(cli_init)
app.command("dev", help="🔧 Run development pipeline (pipelines + dbt)")(cli_dev)
app.command("start", help="🚀 Start development server with file watching")(cli_start)
app.command("webhooks", help="🔗 Start webhook listener server")(cli_webhooks)

@app.command("version")
def version():
    """Show SBDK.dev version"""
    console.print(Panel(
        Text("SBDK.dev v1.0.0", style="bold green"),
        title="Version",
        style="green"
    ))

if __name__ == "__main__":
    app()