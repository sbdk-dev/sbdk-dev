"""
MCP Tools Implementation

Implements tool handlers that wrap SBDK functionality for AI agent access.
Each tool class provides methods that can be invoked through the MCP server.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from sbdk.environment import EnvironmentManager, EnvironmentTemplate, EnvironmentTarget
from sbdk.exceptions import SBDKError
from sbdk.sources import (
    CSVConnector,
    CSVConnectorConfig,
    FileFormat,
    SamplingConfig,
    SamplingStrategy,
)


class EnvironmentTools:
    """
    Environment management tools for MCP.

    Provides AI agents with environment creation, switching, and status checking.
    """

    def __init__(self, sbdk_home: Optional[Path] = None):
        """
        Initialize environment tools.

        Args:
            sbdk_home: Optional SBDK home directory
        """
        self.sbdk_home = sbdk_home or Path.home() / ".sbdk"
        self.manager = EnvironmentManager(sbdk_home=self.sbdk_home)

    def create_environment(
        self,
        name: str,
        template: str = "basic",
        target: str = "duckdb"
    ) -> Dict[str, Any]:
        """
        Create a new SBDK environment.

        Args:
            name: Environment name
            template: Template to use (basic, analytics, ml)
            target: Target database (duckdb, postgres, bigquery)

        Returns:
            Dict with environment path and configuration

        Example:
            >>> tools = EnvironmentTools()
            >>> result = tools.create_environment("dev", template="analytics")
            >>> print(result["path"])
        """
        try:
            # Convert string to enum
            env_template = EnvironmentTemplate(template)
            env_target = EnvironmentTarget(target)

            env_path = self.manager.create(name, template=env_template, target=env_target)

            return {
                "status": "created",
                "name": name,
                "path": str(env_path),
                "template": template,
                "target": target
            }
        except (ValueError, SBDKError) as e:
            raise ValueError(f"Failed to create environment: {e}")

    def switch_environment(self, name: str) -> Dict[str, Any]:
        """
        Switch to a different environment.

        Args:
            name: Environment name

        Returns:
            Dict with switch confirmation and elapsed time

        Example:
            >>> tools = EnvironmentTools()
            >>> result = tools.switch_environment("dev")
            >>> print(result["active_environment"])
        """
        try:
            self.manager.switch(name)
            env_path = self.sbdk_home / "environments" / name
            return {
                "status": "switched",
                "active_environment": name,
                "environment_path": str(env_path)
            }
        except SBDKError as e:
            raise ValueError(f"Failed to switch environment: {e}")

    def list_environments(self, verbose: bool = False) -> Dict[str, Any]:
        """
        List all available environments.

        Args:
            verbose: Include detailed information

        Returns:
            Dict with list of environments

        Example:
            >>> tools = EnvironmentTools()
            >>> result = tools.list_environments()
            >>> for env in result["environments"]:
            ...     print(env["name"])
        """
        try:
            environments = self.manager.list_environments()
            active_env = self.manager.get_active_environment()

            # Mark active environment
            for env in environments:
                env["active"] = env["name"] == active_env

            return {
                "environments": environments,
                "total": len(environments),
                "active": active_env
            }
        except SBDKError as e:
            raise ValueError(f"Failed to list environments: {e}")

    def get_status(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Get current environment status.

        Args:
            verbose: Include detailed information

        Returns:
            Dict with environment status

        Example:
            >>> tools = EnvironmentTools()
            >>> status = tools.get_status()
            >>> print(status["active_environment"])
        """
        try:
            status = self.manager.get_status()
            return status
        except SBDKError as e:
            raise ValueError(f"Failed to get status: {e}")


class SourceTools:
    """
    Data source management tools for MCP.

    Provides AI agents with data source configuration, testing, and schema inspection.
    """

    def __init__(self, sbdk_home: Optional[Path] = None):
        """
        Initialize source tools.

        Args:
            sbdk_home: Optional SBDK home directory
        """
        self.sbdk_home = sbdk_home or Path.home() / ".sbdk"
        self.sources_dir = self.sbdk_home / "sources"
        self.sources_dir.mkdir(parents=True, exist_ok=True)

    def add_source(
        self,
        name: str,
        source_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a new data source.

        Args:
            name: Data source name
            source_type: Type of source (csv, postgres, json)
            config: Source-specific configuration

        Returns:
            Dict with source confirmation

        Example:
            >>> tools = SourceTools()
            >>> result = tools.add_source(
            ...     "users",
            ...     "csv",
            ...     {"file_path": "/data/users.csv"}
            ... )
        """
        try:
            # Save source configuration
            source_config = {
                "name": name,
                "type": source_type,
                "config": config
            }

            source_file = self.sources_dir / f"{name}.json"
            source_file.write_text(json.dumps(source_config, indent=2))

            return {
                "status": "added",
                "name": name,
                "type": source_type,
                "config_path": str(source_file)
            }
        except Exception as e:
            raise ValueError(f"Failed to add source: {e}")

    def test_source(self, name: str) -> Dict[str, Any]:
        """
        Test data source connection.

        Args:
            name: Data source name

        Returns:
            Dict with connection test result

        Example:
            >>> tools = SourceTools()
            >>> result = tools.test_source("users")
            >>> print(result["connected"])
        """
        try:
            # Load source configuration
            source_file = self.sources_dir / f"{name}.json"
            if not source_file.exists():
                raise ValueError(f"Source '{name}' not found")

            source_config = json.loads(source_file.read_text())

            # Test connection based on type
            if source_config["type"] == "csv" or source_config["type"] == "json":
                file_path = Path(source_config["config"].get("file_path", ""))
                if not file_path.exists():
                    return {
                        "connected": False,
                        "error": f"File not found: {file_path}"
                    }

                # Try to read file
                config = CSVConnectorConfig(name=name)
                connector = CSVConnector(config, file_path)
                connector.connect()
                is_connected = connector.test_connection()
                connector.disconnect()

                return {
                    "connected": is_connected,
                    "name": name,
                    "type": source_config["type"]
                }
            else:
                return {
                    "connected": False,
                    "error": f"Testing not implemented for type: {source_config['type']}"
                }

        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    def get_schema(
        self,
        name: str,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get data source schema information.

        Args:
            name: Data source name
            table_name: Optional specific table name

        Returns:
            Dict with schema information

        Example:
            >>> tools = SourceTools()
            >>> schema = tools.get_schema("users")
            >>> for col in schema["columns"]:
            ...     print(f"{col['name']}: {col['type']}")
        """
        try:
            # Load source configuration
            source_file = self.sources_dir / f"{name}.json"
            if not source_file.exists():
                raise ValueError(f"Source '{name}' not found")

            source_config = json.loads(source_file.read_text())

            # Get schema based on type
            if source_config["type"] in ["csv", "json"]:
                file_path = Path(source_config["config"].get("file_path", ""))
                config = CSVConnectorConfig(name=name)
                connector = CSVConnector(config, file_path)
                connector.connect()
                schema = connector.detect_schema(table_name=table_name)
                connector.disconnect()

                return {
                    "table_name": schema.table_name,
                    "columns": schema.columns,
                    "row_count": schema.row_count
                }
            else:
                return {
                    "error": f"Schema detection not implemented for type: {source_config['type']}"
                }

        except Exception as e:
            raise ValueError(f"Failed to get schema: {e}")

    def list_sources(self, verbose: bool = False) -> Dict[str, Any]:
        """
        List all configured data sources.

        Args:
            verbose: Include detailed information

        Returns:
            Dict with list of sources

        Example:
            >>> tools = SourceTools()
            >>> result = tools.list_sources()
            >>> for source in result["sources"]:
            ...     print(source["name"])
        """
        try:
            sources = []
            for source_file in self.sources_dir.glob("*.json"):
                source_config = json.loads(source_file.read_text())
                source_info = {
                    "name": source_config["name"],
                    "type": source_config["type"]
                }
                if verbose:
                    source_info["config"] = source_config["config"]
                sources.append(source_info)

            return {
                "sources": sources,
                "total": len(sources)
            }
        except Exception as e:
            raise ValueError(f"Failed to list sources: {e}")


class QueryTools:
    """
    Query execution tools for MCP.

    Provides AI agents with SQL query execution and data sampling capabilities.
    """

    def __init__(self, sbdk_home: Optional[Path] = None):
        """
        Initialize query tools.

        Args:
            sbdk_home: Optional SBDK home directory
        """
        self.sbdk_home = sbdk_home or Path.home() / ".sbdk"
        self.source_tools = SourceTools(sbdk_home=sbdk_home)

    def execute_query(self, sql: str, limit: int = 100) -> Dict[str, Any]:
        """
        Execute SQL query in current environment.

        Args:
            sql: SQL query to execute
            limit: Maximum rows to return

        Returns:
            Dict with query results

        Note:
            This is a placeholder implementation. Full SQL execution
            requires DuckDB integration which will be added in later phase.

        Example:
            >>> tools = QueryTools()
            >>> result = tools.execute_query("SELECT * FROM users LIMIT 10")
            >>> print(result["rows"])
        """
        return {
            "status": "not_implemented",
            "message": "SQL execution requires DuckDB integration (Phase 1.2+)",
            "sql": sql,
            "limit": limit
        }

    def sample_data(
        self,
        source_name: str,
        strategy: str = "limit",
        limit: int = 100,
        percentage: float = 10.0
    ) -> Dict[str, Any]:
        """
        Sample data from a source.

        Args:
            source_name: Data source name
            strategy: Sampling strategy (full, limit, percentage, random)
            limit: Number of rows (for limit strategy)
            percentage: Percentage to sample (for percentage/random)

        Returns:
            Dict with sampled data

        Example:
            >>> tools = QueryTools()
            >>> result = tools.sample_data("users", strategy="limit", limit=10)
            >>> print(result["rows"])
        """
        try:
            # Load source configuration
            sources_dir = self.sbdk_home / "sources"
            source_file = sources_dir / f"{source_name}.json"
            if not source_file.exists():
                raise ValueError(f"Source '{source_name}' not found")

            source_config = json.loads(source_file.read_text())

            if source_config["type"] in ["csv", "json"]:
                file_path = Path(source_config["config"].get("file_path", ""))

                # Create sampling config
                sampling_strategy = SamplingStrategy(strategy.lower())
                sampling_config = SamplingConfig(
                    strategy=sampling_strategy,
                    limit=limit,
                    percentage=percentage
                )

                # Sample data
                config = CSVConnectorConfig(name=source_name)
                connector = CSVConnector(config, file_path)
                connector.connect()
                sample = list(connector.get_sample(sampling_config))
                connector.disconnect()

                return {
                    "source": source_name,
                    "strategy": strategy,
                    "rows": sample,
                    "count": len(sample)
                }
            else:
                return {
                    "error": f"Sampling not implemented for type: {source_config['type']}"
                }

        except Exception as e:
            raise ValueError(f"Failed to sample data: {e}")


class SchemaTools:
    """
    Schema browsing tools for MCP.

    Provides AI agents with schema discovery and inspection capabilities.
    """

    def __init__(self, sbdk_home: Optional[Path] = None):
        """
        Initialize schema tools.

        Args:
            sbdk_home: Optional SBDK home directory
        """
        self.sbdk_home = sbdk_home or Path.home() / ".sbdk"
        self.source_tools = SourceTools(sbdk_home=sbdk_home)

    def browse_schemas(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Browse available schemas and tables.

        Args:
            environment: Environment name (uses current if not specified)

        Returns:
            Dict with available schemas

        Example:
            >>> tools = SchemaTools()
            >>> schemas = tools.browse_schemas()
            >>> for schema in schemas["schemas"]:
            ...     print(schema["name"])
        """
        try:
            # List all sources as available "schemas"
            sources_result = self.source_tools.list_sources(verbose=False)

            return {
                "schemas": [
                    {"name": source["name"], "type": source["type"]}
                    for source in sources_result["sources"]
                ],
                "total": sources_result["total"]
            }
        except Exception as e:
            raise ValueError(f"Failed to browse schemas: {e}")

    def inspect_table(
        self,
        table_name: str,
        include_sample: bool = True
    ) -> Dict[str, Any]:
        """
        Inspect detailed table schema.

        Args:
            table_name: Table name to inspect (source name)
            include_sample: Include sample data

        Returns:
            Dict with table schema and optional sample

        Example:
            >>> tools = SchemaTools()
            >>> table = tools.inspect_table("users", include_sample=True)
            >>> print(table["schema"]["columns"])
        """
        try:
            # Get schema
            schema = self.source_tools.get_schema(table_name)

            result = {
                "table_name": table_name,
                "schema": schema
            }

            # Add sample if requested
            if include_sample:
                query_tools = QueryTools(sbdk_home=self.sbdk_home)
                sample = query_tools.sample_data(table_name, strategy="limit", limit=5)
                result["sample"] = sample.get("rows", [])

            return result
        except Exception as e:
            raise ValueError(f"Failed to inspect table: {e}")
