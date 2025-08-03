"""
Webhook server management
"""

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def cli_webhooks(
    port: int = typer.Option(8000, help="Port to run webhook server on"),
    reload: bool = typer.Option(True, help="Enable auto-reload"),
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
):
    """Start FastAPI webhook listener server"""

    # Check if FastAPI server exists
    server_path = Path("fastapi_server/webhook_listener.py")
    if not server_path.exists():
        console.print(
            "[red]FastAPI server not found. Make sure you're in a SBDK project directory.[/red]"
        )
        raise typer.Exit(1)

    console.print(
        Panel(
            f"[green]🚀 Starting webhook server...[/green]\n\n"
            f"[cyan]Server:[/cyan] http://{host}:{port}\n"
            f"[cyan]Webhook endpoint:[/cyan] http://{host}:{port}/webhook/github\n"
            f"[cyan]Health check:[/cyan] http://{host}:{port}/health\n\n"
            "[dim]Press Ctrl+C to stop[/dim]",
            title="🔗 Webhook Server",
            style="blue",
        )
    )

    try:
        # Start uvicorn server
        cmd = [
            "uvicorn",
            "fastapi_server.webhook_listener:app",
            "--host",
            host,
            "--port",
            str(port),
        ]

        if reload:
            cmd.append("--reload")

        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to start webhook server: {e}[/red]")
        raise typer.Exit(1) from e
    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 Webhook server stopped[/yellow]")
