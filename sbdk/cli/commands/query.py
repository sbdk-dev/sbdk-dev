"""
Database query command
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def cli_query(
    sql: Optional[str] = typer.Argument(None, help="SQL query to execute"),
    interactive: bool = typer.Option(False, "-i", "--interactive", help="Start interactive mode"),
    config: str = typer.Option("sbdk_config.json", help="Path to config file"),
):
    """Query the project's DuckDB database"""

    try:
        import duckdb
    except ImportError:
        console.print("[red]❌ DuckDB not found. Install with: pip install duckdb[/red]")
        raise typer.Exit(1)

    # Find database file
    if not Path(config).exists():
        console.print(
            "[red]Config file not found. Run 'sbdk init' first.[/red]"
        )
        raise typer.Exit(1)

    import json
    with open(config) as f:
        config_data = json.load(f)

    db_path = Path(config_data.get("duckdb_path", "data/project.duckdb"))

    if not db_path.exists():
        console.print(
            f"[red]❌ Database not found: {db_path}[/red]\n"
            "[yellow]💡 Run 'sbdk run' to create the database[/yellow]"
        )
        raise typer.Exit(1)

    console.print(f"[cyan]📂 Using database: {db_path}[/cyan]")

    # Connect to database
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
    except Exception as e:
        console.print(f"[red]❌ Failed to connect: {e}[/red]")
        raise typer.Exit(1)

    try:
        if interactive:
            # Interactive mode
            _interactive_mode(conn)
        elif sql:
            # Execute SQL query
            _execute_query(conn, sql)
        else:
            # Show tables (default)
            _show_tables(conn)

    finally:
        conn.close()


def _show_tables(conn):
    """Display all tables with row counts"""
    console.print("\n[bold cyan]📊 Available Tables[/bold cyan]")

    tables = conn.execute("SHOW TABLES").fetchall()

    if not tables:
        console.print("[yellow]  No tables found. Run 'sbdk run' to generate data.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Table Name", style="cyan")
    table.add_column("Row Count", justify="right", style="green")

    total_rows = 0
    for tbl in tables:
        table_name = tbl[0]
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        total_rows += row_count
        table.add_row(table_name, f"{row_count:,}")

    console.print(table)
    console.print(f"\n[bold]Total rows:[/bold] [green]{total_rows:,}[/green]")
    console.print("\n[dim]💡 Run 'sbdk query \"SELECT * FROM table_name\"' to query data[/dim]")


def _execute_query(conn, sql: str):
    """Execute a SQL query and display results"""
    console.print(f"\n[cyan]🔍 Executing:[/cyan] {sql}\n")

    try:
        result = conn.execute(sql).fetchdf()

        if result.empty:
            console.print("[yellow]  No results returned.[/yellow]")
        else:
            # Create rich table
            table = Table(show_header=True, header_style="bold magenta")

            # Add columns
            for col in result.columns:
                table.add_column(str(col), style="cyan")

            # Add rows (limit to 100 for display)
            for idx, row in result.iterrows():
                if idx >= 100:
                    console.print(f"\n[yellow]... showing first 100 of {len(result)} rows[/yellow]")
                    break
                table.add_row(*[str(val) for val in row])

            console.print(table)
            console.print(f"\n[green]✅ Returned {len(result)} row(s)[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


def _interactive_mode(conn):
    """Interactive SQL prompt"""
    console.print("\n[bold cyan]🔄 Interactive Mode[/bold cyan]")
    console.print("[dim]Enter SQL queries (type 'exit' or 'quit' to exit)[/dim]")
    console.print("[dim]Type 'tables' to show all tables[/dim]\n")

    while True:
        try:
            sql = console.input("[bold cyan]duckdb>[/bold cyan] ").strip()

            if not sql:
                continue

            if sql.lower() in ('exit', 'quit', 'q'):
                console.print("[yellow]👋 Goodbye![/yellow]")
                break

            if sql.lower() == 'tables':
                _show_tables(conn)
                continue

            _execute_query(conn, sql)

        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]👋 Goodbye![/yellow]")
            break
