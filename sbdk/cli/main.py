#!/usr/bin/env python3
"""
SBDK.dev CLI - Modern data pipeline sandbox toolkit

Enhanced with Phase 2 improvements:
- Global options (--verbose, --quiet, --dry-run, --format)
- Context management integration
- Structured error handling
- Professional CLI patterns
"""
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from sbdk.cli.commands.dev import cli_dev
from sbdk.cli.commands.init import cli_init
from sbdk.cli.commands.query import cli_query
from sbdk.cli.commands.run import cli_run
from sbdk.cli.commands.webhooks import cli_webhooks
from sbdk.cli.debug import cli_debug
from sbdk.context import create_context

console = Console()

# Create app with enhanced configuration
app = typer.Typer(
    name="sbdk",
    help="🚀 SBDK.dev - Local-first data pipeline sandbox",
    rich_markup_mode="rich",
    add_completion=True,  # Enable shell completion
    no_args_is_help=True,  # Show help if no args
)


# Global state for shared options
class GlobalOptions:
    """Container for global CLI options."""
    verbose: bool = False
    quiet: bool = False
    dry_run: bool = False
    output_format: str = "text"
    project_dir: Optional[Path] = None


global_options = GlobalOptions()


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output with detailed logging"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output (errors only)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview actions without executing (show what would happen)"
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json, yaml, table, minimal"
    ),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project directory (default: current directory)",
        exists=False  # Don't validate existence for init command
    ),
):
    """
    SBDK.dev - Build data pipelines with DLT, DuckDB, and dbt

    Global Options:
        --verbose/-v: Show detailed debug information
        --quiet/-q: Minimal output (errors only)
        --dry-run: Preview mode (no actual changes)
        --format/-f: Output format (text, json, yaml, table, minimal)
        --project-dir/-p: Specify project directory

    Examples:
        # Initialize new project with verbose output
        sbdk --verbose init my_project

        # Run pipeline with JSON output
        sbdk --format json run

        # Preview pipeline execution without running
        sbdk --dry-run run

        # Quiet mode for scripting
        sbdk --quiet run --pipelines-only
    """
    # Store global options
    global_options.verbose = verbose
    global_options.quiet = quiet
    global_options.dry_run = dry_run
    global_options.output_format = output_format
    global_options.project_dir = project_dir or Path.cwd()

    # Create context for command execution
    if ctx.invoked_subcommand not in ["version", None]:
        # Initialize context (but don't verify project for init command)
        sbdk_ctx = create_context(
            project_dir=global_options.project_dir,
            verbose=verbose,
            quiet=quiet,
            dry_run=dry_run
        )

        # Store context in Typer context for subcommands
        ctx.obj = sbdk_ctx

        if verbose:
            sbdk_ctx.logger.debug(f"SBDK CLI initialized")
            sbdk_ctx.logger.debug(f"Project directory: {global_options.project_dir}")
            sbdk_ctx.logger.debug(f"Output format: {output_format}")

        if dry_run:
            sbdk_ctx.logger.info("🔍 DRY RUN MODE: No changes will be made")


# Register CLI commands
app.command("init", help="🏗️ Initialize a new SBDK project")(cli_init)
app.command("run", help="🚀 Execute data pipeline")(cli_run)
app.command("query", help="🔍 Query DuckDB database")(cli_query)
app.add_typer(cli_dev, name="dev", help="🔧 Execute pipeline in development mode")
app.command("webhooks", help="🔗 Start webhook listener server")(cli_webhooks)
app.command("debug", help="🔍 Debug SBDK configuration and environment")(cli_debug)


@app.command("interactive")
def interactive():
    """🎯 Start interactive CLI interface"""
    from sbdk.cli.interactive import start_interactive
    start_interactive(".")


@app.command("version")
def version():
    """Show SBDK.dev version and environment information"""
    from sbdk import __version__
    import sys
    import platform

    if global_options.output_format == "json":
        import json
        version_info = {
            "version": __version__,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "python_path": sys.executable
        }
        console.print(json.dumps(version_info, indent=2))
    elif global_options.output_format == "minimal":
        console.print(__version__)
    else:
        version_text = f"SBDK.dev v{__version__}"

        if global_options.verbose:
            version_text += f"\n\nPython: {sys.version.split()[0]}"
            version_text += f"\nPlatform: {platform.platform()}"
            version_text += f"\nExecutable: {sys.executable}"

        console.print(
            Panel(
                Text(version_text, style="bold green"),
                title="Version",
                style="green",
            )
        )


@app.command("completion")
def completion(
    shell: str = typer.Argument(
        "bash",
        help="Shell type: bash, zsh, fish, powershell"
    )
):
    """
    Generate shell completion script

    Examples:
        # Bash
        sbdk completion bash > ~/.sbdk-completion.bash
        echo 'source ~/.sbdk-completion.bash' >> ~/.bashrc

        # Zsh
        sbdk completion zsh > ~/.sbdk-completion.zsh
        echo 'source ~/.sbdk-completion.zsh' >> ~/.zshrc

        # Fish
        sbdk completion fish > ~/.config/fish/completions/sbdk.fish
    """
    from sbdk.formatters import create_formatter

    formatter = create_formatter(quiet=global_options.quiet)

    shell = shell.lower()
    valid_shells = ["bash", "zsh", "fish", "powershell"]

    if shell not in valid_shells:
        formatter.error(
            f"Unsupported shell: {shell}",
            suggestion=f"Use one of: {', '.join(valid_shells)}"
        )
        raise typer.Exit(1)

    # Generate completion script
    try:
        import click
        # Get the Click context from Typer
        # This is a simplified version - full implementation would use typer_click_object
        formatter.info(
            f"Completion script for {shell}",
            details={
                "shell": shell,
                "note": "Save output to appropriate completion file location"
            }
        )

        # For now, provide instructions
        instructions = {
            "bash": "Add to ~/.bashrc: eval \"$(_SBDK_COMPLETE=bash_source sbdk)\"",
            "zsh": "Add to ~/.zshrc: eval \"$(_SBDK_COMPLETE=zsh_source sbdk)\"",
            "fish": "Add to ~/.config/fish/completions/sbdk.fish: eval (env _SBDK_COMPLETE=fish_source sbdk)",
            "powershell": "See typer documentation for PowerShell completion setup"
        }

        console.print(f"\n[cyan]Setup Instructions for {shell}:[/cyan]")
        console.print(f"  {instructions[shell]}")

    except Exception as e:
        formatter.error(
            f"Failed to generate completion: {e}",
            suggestion="Ensure typer and click are properly installed"
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
