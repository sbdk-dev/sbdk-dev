"""
MCP Server CLI Commands

Provides command-line interface for managing the SBDK MCP server.
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table

from sbdk.mcp import MCPServer

app = typer.Typer(help="MCP (Model Context Protocol) server management")
console = Console()


@app.command()
def list_tools(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed tool information"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)")
) -> None:
    """
    List all available MCP tools.

    Example:
        sbdk mcp list-tools
        sbdk mcp list-tools --verbose
        sbdk mcp list-tools --format json
    """
    try:
        server = MCPServer()
        tools = server.list_tools()

        if output_format == "json":
            console.print(JSON(json.dumps(tools, indent=2)))
            return

        # Create table
        table = Table(title=f"SBDK MCP Tools ({len(tools)} available)")
        table.add_column("Tool Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")

        if verbose:
            table.add_column("Parameters", style="yellow")

        for tool in sorted(tools, key=lambda t: t["name"]):
            if verbose:
                params = json.dumps(tool["parameters"], indent=2)
                table.add_row(tool["name"], tool["description"], params)
            else:
                table.add_row(tool["name"], tool["description"])

        console.print(table)
        console.print(f"\n[dim]Use 'sbdk mcp info <tool-name>' for detailed tool information[/]")

    except Exception as e:
        console.print(f"[red]Error listing tools: {e}[/]")
        raise typer.Exit(1)


@app.command()
def info(
    tool_name: str = typer.Argument(..., help="Tool name to get information about")
) -> None:
    """
    Get detailed information about a specific MCP tool.

    Example:
        sbdk mcp info env_create
        sbdk mcp info query_execute
    """
    try:
        server = MCPServer()
        tool_info = server.get_tool_info(tool_name)

        if not tool_info:
            console.print(f"[red]Tool '{tool_name}' not found[/]")
            console.print("\n[dim]Use 'sbdk mcp list-tools' to see available tools[/]")
            raise typer.Exit(1)

        # Display tool information
        console.print(Panel.fit(
            f"[bold cyan]{tool_info['name']}[/]\n\n"
            f"[green]{tool_info['description']}[/]",
            border_style="cyan",
            title="Tool Information"
        ))

        # Display parameters
        console.print("\n[bold yellow]Parameters:[/]")
        params = tool_info["parameters"]

        if "properties" in params:
            for param_name, param_info in params["properties"].items():
                is_required = param_name in params.get("required", [])
                required_marker = "[red]*[/]" if is_required else ""
                param_type = param_info.get("type", "unknown")
                param_desc = param_info.get("description", "No description")
                default = param_info.get("default", "")
                default_str = f" (default: {default})" if default else ""

                console.print(
                    f"  {required_marker}[cyan]{param_name}[/] "
                    f"[dim]({param_type})[/]: {param_desc}{default_str}"
                )

                # Show enum values if available
                if "enum" in param_info:
                    console.print(f"    [dim]Values: {', '.join(param_info['enum'])}[/]")
        else:
            console.print("  [dim]No parameters[/]")

    except Exception as e:
        console.print(f"[red]Error getting tool info: {e}[/]")
        raise typer.Exit(1)


@app.command()
def test(
    tool_name: str = typer.Argument(..., help="Tool name to test"),
    params: str = typer.Option("{}", "--params", "-p", help="JSON parameters for the tool")
) -> None:
    """
    Test an MCP tool with given parameters.

    Example:
        sbdk mcp test env_list
        sbdk mcp test env_create --params '{"name": "test", "template": "basic"}'
        sbdk mcp test source_list --params '{"verbose": true}'
    """
    try:
        server = MCPServer()

        # Parse parameters
        try:
            parameters = json.loads(params)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON parameters: {e}[/]")
            raise typer.Exit(1)

        # Invoke tool
        console.print(f"[yellow]→ Invoking tool: {tool_name}[/]")
        console.print(f"[dim]Parameters: {parameters}[/]\n")

        result = server.invoke_tool(tool_name, parameters)

        if result.success:
            console.print("[green]✓ Tool executed successfully[/]\n")
            console.print("[bold]Result:[/]")
            console.print(JSON(json.dumps(result.data, indent=2)))
        else:
            console.print(f"[red]✗ Tool execution failed[/]")
            console.print(f"[red]Error: {result.error}[/]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error testing tool: {e}[/]")
        raise typer.Exit(1)


@app.command()
def export_manifest(
    output: Path = typer.Option(
        Path("mcp_manifest.json"),
        "--output",
        "-o",
        help="Output file path"
    )
) -> None:
    """
    Export MCP server manifest (tool definitions for AI agents).

    The manifest contains all tool definitions in a format that AI agents
    can use to discover and invoke SBDK capabilities.

    Example:
        sbdk mcp export-manifest
        sbdk mcp export-manifest --output my_manifest.json
    """
    try:
        server = MCPServer()
        manifest = server.export_manifest(output_path=output)

        console.print(f"[green]✓ Exported manifest to {output}[/]")
        console.print(f"\n[dim]Total tools: {len(manifest['tools'])}[/]")

        # Show summary
        console.print("\n[bold]Tool Categories:[/]")
        categories = {}
        for tool in manifest["tools"]:
            category = tool["name"].split("_")[0]
            categories[category] = categories.get(category, 0) + 1

        for category, count in sorted(categories.items()):
            console.print(f"  {category}: {count} tools")

    except Exception as e:
        console.print(f"[red]Error exporting manifest: {e}[/]")
        raise typer.Exit(1)


@app.command()
def validate() -> None:
    """
    Validate MCP server configuration and tools.

    Performs a series of checks to ensure the MCP server is
    properly configured and all tools are accessible.

    Example:
        sbdk mcp validate
    """
    try:
        console.print("[yellow]→ Validating MCP server...[/]\n")

        server = MCPServer()

        # Check 1: Tools loaded
        tools = server.list_tools()
        if tools:
            console.print(f"[green]✓ Loaded {len(tools)} tools[/]")
        else:
            console.print("[red]✗ No tools loaded[/]")
            raise typer.Exit(1)

        # Check 2: Tool categories
        categories = set(tool["name"].split("_")[0] for tool in tools)
        expected_categories = {"env", "source", "query", "schema"}

        if expected_categories.issubset(categories):
            console.print(f"[green]✓ All expected tool categories present[/]")
        else:
            missing = expected_categories - categories
            console.print(f"[yellow]⚠ Missing tool categories: {missing}[/]")

        # Check 3: Test a simple tool
        console.print("\n[yellow]→ Testing tools...[/]")

        # Test env_status (should always work)
        result = server.invoke_tool("env_status", {"verbose": False})
        if result.success:
            console.print("[green]✓ Tool invocation works[/]")
        else:
            console.print(f"[red]✗ Tool invocation failed: {result.error}[/]")
            raise typer.Exit(1)

        # Success
        console.print("\n[green]✓ MCP server validation passed[/]")
        console.print("\n[dim]Server is ready for AI agent integration[/]")

    except Exception as e:
        console.print(f"\n[red]✗ Validation failed: {e}[/]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
