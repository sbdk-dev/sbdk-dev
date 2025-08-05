#!/usr/bin/env python3
"""
SBDK.dev Interactive CLI
A clean, functional interface for data pipeline management
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.columns import Columns

console = Console()


class SBDKInteractive:
    """Clean, functional interactive CLI for SBDK"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.config = self._load_config()
        self.running = True
        
    def _load_config(self) -> dict:
        """Load SBDK configuration"""
        config_path = self.project_path / "sbdk_config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception:
                pass
        # Try to detect project name for default config
        project_name = self.project_path.name if self.project_path.name != "." else "dev"
        return {
            "project": project_name,
            "target": "dev", 
            "duckdb_path": f"data/{project_name}.duckdb",
            "pipelines_path": "./pipelines",
            "dbt_path": "./dbt"
        }
    
    def _get_project_status(self) -> dict:
        """Get current project status"""
        status = {}
        
        # Check database
        db_path = self.project_path / self.config.get("duckdb_path", "data/dev.duckdb")
        status["database"] = {
            "exists": db_path.exists(),
            "path": str(db_path),
            "size": f"{db_path.stat().st_size / (1024*1024):.1f} MB" if db_path.exists() else "0 MB"
        }
        
        # Check pipelines
        pipelines_path = self.project_path / "pipelines"
        if pipelines_path.exists():
            pipeline_files = list(pipelines_path.glob("*.py"))
            status["pipelines"] = {
                "count": len([f for f in pipeline_files if not f.name.startswith("_")]),
                "files": [f.stem for f in pipeline_files if not f.name.startswith("_")]
            }
        else:
            status["pipelines"] = {"count": 0, "files": []}
            
        # Check dbt
        dbt_path = self.project_path / "dbt"
        if dbt_path.exists():
            models_path = dbt_path / "models"
            if models_path.exists():
                model_files = list(models_path.rglob("*.sql"))
                status["dbt"] = {
                    "models": len(model_files),
                    "files": [f.stem for f in model_files]
                }
            else:
                status["dbt"] = {"models": 0, "files": []}
        else:
            status["dbt"] = {"models": 0, "files": []}
            
        return status
    
    def _create_header(self) -> Panel:
        """Create header panel"""
        from sbdk import __version__
        project_name = self.config.get("project", "Unknown Project")
        
        header_text = Text()
        header_text.append("🚀 SBDK.dev Interactive CLI ", style="bold blue")
        header_text.append(f"v{__version__}", style="dim")
        header_text.append(f"\n📁 Project: {project_name}", style="cyan")
        
        return Panel(
            Align.center(header_text),
            style="blue",
            height=3
        )
    
    def _create_status_panel(self) -> Panel:
        """Create project status panel"""
        status = self._get_project_status()
        
        table = Table(show_header=False, show_edge=False, pad_edge=False)
        table.add_column("Item", style="cyan", width=15)
        table.add_column("Status", style="white", width=25)
        
        # Database status
        db_icon = "🟢" if status["database"]["exists"] else "🔴"
        table.add_row(
            "Database",
            f"{db_icon} {status['database']['size']} ({status['database']['path']})"
        )
        
        # Pipelines status
        pipeline_count = status["pipelines"]["count"]
        pipeline_icon = "🟢" if pipeline_count > 0 else "🟡"
        table.add_row(
            "Pipelines", 
            f"{pipeline_icon} {pipeline_count} files ({', '.join(status['pipelines']['files'][:3])}{'...' if len(status['pipelines']['files']) > 3 else ''})"
        )
        
        # dbt status
        model_count = status["dbt"]["models"]
        dbt_icon = "🟢" if model_count > 0 else "🟡"
        table.add_row(
            "dbt Models",
            f"{dbt_icon} {model_count} models"
        )
        
        return Panel(table, title="📊 Project Status", title_align="left")
    
    def _create_menu_panel(self) -> Panel:
        """Create main menu panel"""
        menu_text = Text()
        
        menu_items = [
            ("1", "Run full pipeline (DLT + dbt)", "green"),
            ("2", "Run pipelines only", "yellow"), 
            ("3", "Run dbt only", "blue"),
            ("4", "Watch mode (auto-run on changes)", "magenta"),
            ("5", "View database (DuckDB shell)", "cyan"),
            ("6", "Project info", "white"),
            ("q", "Quit", "red")
        ]
        
        for key, desc, color in menu_items:
            menu_text.append(f"[{key}] ", style=f"bold {color}")
            menu_text.append(f"{desc}\n", style="white")
            
        return Panel(menu_text, title="🎯 Actions", title_align="left")
    
    def _create_footer(self) -> Panel:
        """Create footer with tips"""
        footer_text = Text()
        footer_text.append("💡 Tips: ", style="bold yellow")
        footer_text.append("Use 'sbdk init <project>' to create new projects • ", style="dim")
        footer_text.append("Press any key to choose an action", style="dim")
        
        return Panel(footer_text, style="dim", height=3)
    
    
    def _run_command(self, description: str, command: list, show_output: bool = True) -> bool:
        """Run a command with nice UI feedback"""
        console.print(f"\n[cyan]{description}...[/cyan]")
        
        try:
            if show_output:
                # Run with live output
                result = subprocess.run(command, cwd=self.project_path, check=True)
            else:
                # Run with captured output
                result = subprocess.run(
                    command, 
                    cwd=self.project_path, 
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            console.print(f"[green]✅ {description} completed successfully![/green]")
            return True
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ {description} failed![/red]")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[dim]{e.stderr}[/dim]")
            return False
    
    def _handle_run_full(self):
        """Handle full pipeline run"""
        console.clear()
        console.print("[bold]🚀 Running Full Pipeline[/bold]\n")
        
        success = self._run_command(
            "Running DLT pipelines + dbt transformations",
            ["uv", "run", "sbdk", "run"]
        )
        
        if success:
            console.print("\n[green]Pipeline completed! Database updated with fresh data.[/green]")
        else:
            console.print("\n[red]Pipeline failed. Check the output above for details.[/red]")
        
        console.print("\n[dim]Press any key to continue...[/dim]")
        console.input()
    
    def _handle_run_pipelines(self):
        """Handle pipelines only run"""
        console.clear()
        console.print("[bold]⚡ Running Pipelines Only[/bold]\n")
        
        success = self._run_command(
            "Running DLT pipelines",
            ["uv", "run", "sbdk", "run", "--pipelines-only"]
        )
        
        if success:
            console.print("\n[green]Pipelines completed! Raw data loaded to database.[/green]")
        else:
            console.print("\n[red]Pipelines failed. Check the output above for details.[/red]")
            
        console.print("\n[dim]Press any key to continue...[/dim]")
        console.input()
    
    def _handle_run_dbt(self):
        """Handle dbt only run"""
        console.clear()
        console.print("[bold]🏗️ Running dbt Only[/bold]\n")
        
        success = self._run_command(
            "Running dbt transformations",
            ["uv", "run", "sbdk", "run", "--dbt-only"]
        )
        
        if success:
            console.print("\n[green]dbt transformations completed! Analytics tables updated.[/green]")
            
        console.print("\n[dim]Press any key to continue...[/dim]")
        console.input()
    
    def _handle_watch_mode(self):
        """Handle watch mode"""
        console.clear()
        console.print("[bold]👀 Starting Watch Mode[/bold]")
        console.print("[dim]Watching for file changes... Press Ctrl+C to stop[/dim]\n")
        
        try:
            subprocess.run(
                ["uv", "run", "sbdk", "run", "--watch"],
                cwd=self.project_path
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Watch mode stopped.[/yellow]")
            
        console.print("\n[dim]Press any key to continue...[/dim]")
        console.input()
    
    def _handle_database_shell(self):
        """Handle database shell"""
        db_path = self.project_path / self.config.get("duckdb_path", "data/dev.duckdb")
        
        if not db_path.exists():
            console.print("[red]Database not found. Run pipeline first.[/red]")
            console.print("\n[dim]Press any key to continue...[/dim]")
            console.input()
            return
            
        console.clear()
        console.print("[bold]🦆 Opening DuckDB Shell[/bold]")
        console.print(f"[dim]Database: {db_path}[/dim]")
        console.print("[dim]Type .quit to exit the database shell[/dim]\n")
        
        try:
            # Try to use system duckdb CLI first
            subprocess.run(["duckdb", str(db_path)], cwd=self.project_path)
        except FileNotFoundError:
            # Fall back to Python-based DuckDB shell
            try:
                import duckdb
                console.print("[yellow]Using Python DuckDB shell (CLI not found)[/yellow]")
                console.print("[dim]Enter SQL queries or .quit to exit[/dim]\n")
                
                conn = duckdb.connect(str(db_path))
                
                while True:
                    try:
                        query = console.input("[bold blue]duckdb>[/bold blue] ")
                        if query.strip().lower() in ['.quit', '.exit', 'quit', 'exit']:
                            break
                        if query.strip():
                            result = conn.execute(query).fetchall()
                            if result:
                                from rich.table import Table
                                table = Table()
                                # Get column names
                                columns = [desc[0] for desc in conn.description]
                                for col in columns:
                                    table.add_column(col)
                                for row in result:
                                    table.add_row(*[str(cell) for cell in row])
                                console.print(table)
                            else:
                                console.print("[green]Query executed successfully[/green]")
                    except (KeyboardInterrupt, EOFError):
                        break
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                
                conn.close()
            except ImportError:
                console.print("[red]DuckDB Python package not found. Install with: uv add duckdb[/red]")
                console.print("\n[dim]Press any key to continue...[/dim]")
                console.input()
        except KeyboardInterrupt:
            pass
    
    def _handle_project_info(self):
        """Handle project info display"""
        console.clear()
        console.print("[bold]📋 Project Information[/bold]\n")
        
        # Configuration
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")
        
        for key, value in self.config.items():
            config_table.add_row(key, str(value))
        
        console.print(config_table)
        console.print()
        
        # Detailed status
        status = self._get_project_status()
        
        # Pipeline details
        if status["pipelines"]["files"]:
            pipeline_table = Table(title="Available Pipelines")
            pipeline_table.add_column("Pipeline", style="green")
            for pipeline in status["pipelines"]["files"]:
                pipeline_table.add_row(pipeline)
            console.print(pipeline_table)
            console.print()
        
        # dbt details  
        if status["dbt"]["files"]:
            dbt_table = Table(title="dbt Models")
            dbt_table.add_column("Model", style="blue")
            for model in status["dbt"]["files"]:
                dbt_table.add_row(model)
            console.print(dbt_table)
        
        console.print("\n[dim]Press any key to continue...[/dim]")
        console.input()
    
    def _get_user_choice(self) -> str:
        """Get user menu choice"""
        try:
            choice = console.input("\n[bold]Enter your choice: [/bold]").strip().lower()
            return choice
        except (KeyboardInterrupt, EOFError):
            return "q"
    
    def _is_first_run(self) -> bool:
        """Check if this is a first run (no database exists)"""
        status = self._get_project_status()
        return not status["database"]["exists"]
    
    def _show_welcome_flow(self):
        """Show guided welcome flow for first-time users"""
        console.clear()
        console.print("[bold]🎉 Welcome to SBDK.dev![/bold]\n")
        
        console.print("This appears to be your first time running this project.")
        console.print("Let me help you get started!\n")
        
        console.print("[bold cyan]What would you like to do?[/bold cyan]")
        console.print("[1] [green]Run demo with sample data[/green] (Recommended for first-time users)")
        console.print("    • Generates 10K users, 50K events, 20K orders")
        console.print("    • Creates analytics dashboard with dbt")
        console.print("    • Perfect for learning and exploration")
        console.print()
        console.print("[2] [yellow]Set up custom project[/yellow] (For experienced users)")
        console.print("    • Guide you through creating your own pipelines")
        console.print("    • Help configure your data sources")
        console.print("    • Customize dbt models for your use case")
        console.print()
        console.print("[3] [blue]Learn more about SBDK[/blue]")
        console.print("    • View project information and capabilities")
        console.print("    • Understand the architecture")
        console.print("    • See what files are included")
        console.print()
        
        while True:
            choice = console.input("\n[bold]Choose an option (1-3): [/bold]").strip()
            
            if choice == "1":
                return self._handle_demo_setup()
            elif choice == "2":
                return self._handle_custom_setup()
            elif choice == "3":
                return self._handle_learn_more()
            else:
                console.print(f"[red]Please enter 1, 2, or 3[/red]")
    
    def _handle_demo_setup(self):
        """Handle demo setup flow"""
        console.clear()
        console.print("[bold]🚀 Setting up SBDK Demo[/bold]\n")
        
        console.print("The demo will:")
        console.print("• Generate realistic synthetic data (users, events, orders)")
        console.print("• Create a DuckDB database with your data")
        console.print("• Run dbt transformations to create analytics tables")
        console.print("• Show you the complete data pipeline in action")
        console.print()
        
        proceed = console.input("Ready to run the demo? [Y/n]: ").strip().lower()
        if proceed in ['', 'y', 'yes']:
            console.print("\n[green]🎯 Running demo pipeline...[/green]")
            return self._handle_run_full()
        else:
            console.print("\n[yellow]Demo cancelled. You can run it anytime by choosing option 1.[/yellow]")
            time.sleep(2)
            return False
    
    def _handle_custom_setup(self):
        """Handle custom project setup flow"""
        console.clear()
        console.print("[bold]🛠️ Custom Project Setup[/bold]\n")
        
        console.print("To set up your own project:")
        console.print()
        console.print("[bold cyan]1. Modify your pipelines:[/bold cyan]")
        console.print("   • Edit files in pipelines/ directory")
        console.print("   • Replace synthetic data with your real data sources")
        console.print("   • Update the data generation logic")
        console.print()
        console.print("[bold cyan]2. Update dbt models:[/bold cyan]")
        console.print("   • Modify files in dbt/models/ directory")
        console.print("   • Update staging models for your data structure")
        console.print("   • Create custom analytics in marts/")
        console.print()
        console.print("[bold cyan]3. Configure data sources:[/bold cyan]")
        console.print("   • Update sbdk_config.json with your settings")
        console.print("   • Set up any external connections")
        console.print("   • Configure environment variables")
        console.print()
        
        console.print("[green]💡 Tip: Start with the demo to understand the structure,")
        console.print("   then gradually replace components with your own data![/green]")
        
        console.input("\n[dim]Press any key to continue...[/dim]")
        return False
    
    def _handle_learn_more(self):
        """Handle learn more flow"""
        return self._handle_project_info()
    
    def run(self):
        """Main interactive loop with guided flow"""
        console.clear()
        
        # Check if this is first run and show welcome flow
        if self._is_first_run():
            if self._show_welcome_flow():
                # If they ran the demo, continue to main loop
                pass
            else:
                # If they chose another option, return to main loop
                pass
        
        while self.running:
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(self._create_header(), name="header", size=5),
                Layout(name="main", ratio=1),
                Layout(self._create_footer(), name="footer", size=5)
            )
            
            # Split main area
            layout["main"].split_row(
                Layout(self._create_status_panel(), name="status"),
                Layout(self._create_menu_panel(), name="menu")
            )
            
            # Display interface
            console.print(layout)
            
            # Get user choice
            choice = self._get_user_choice()
            
            # Handle choice
            if choice == "1":
                self._handle_run_full()
            elif choice == "2": 
                self._handle_run_pipelines()
            elif choice == "3":
                self._handle_run_dbt()
            elif choice == "4":
                self._handle_watch_mode()
            elif choice == "5":
                self._handle_database_shell()
            elif choice == "6":
                self._handle_project_info()
            elif choice == "q":
                self.running = False
            else:
                console.print(f"[red]Invalid choice: {choice}[/red]")
                time.sleep(1)
            
            if self.running:
                console.clear()
        
        console.print("\n[green]👋 Thanks for using SBDK.dev![/green]")


def start_interactive(project_path: str = "."):
    """Start the interactive CLI"""
    try:
        cli = SBDKInteractive(project_path)
        cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    start_interactive()