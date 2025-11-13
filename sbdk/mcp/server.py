"""
MCP Server Implementation

Implements the Model Context Protocol server for SBDK, exposing tools
that AI agents can use to interact with SBDK functionality.

The MCP protocol defines a standard way for AI models to:
- Discover available tools
- Invoke tools with parameters
- Receive structured responses

References:
    - MCP Specification: https://modelcontextprotocol.io/
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from sbdk.mcp.tools import EnvironmentTools, QueryTools, SchemaTools, SourceTools

logger = logging.getLogger(__name__)


class MCPTool(BaseModel):
    """Definition of an MCP tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for parameters"
    )
    handler: Optional[Callable] = Field(None, exclude=True, description="Tool handler function")


class MCPToolResult(BaseModel):
    """Result of an MCP tool invocation."""

    success: bool = Field(..., description="Whether the tool executed successfully")
    data: Optional[Any] = Field(None, description="Tool output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MCPServer:
    """
    MCP Server for SBDK.

    Provides AI agents with structured access to SBDK capabilities
    through the Model Context Protocol.

    Example:
        >>> server = MCPServer()
        >>> server.run(port=3000)

    Available Tools:
        Environment Management:
            - env_create: Create new environment
            - env_switch: Switch to environment
            - env_list: List all environments
            - env_status: Get environment status

        Data Sources:
            - source_add: Add data source
            - source_test: Test source connection
            - source_schema: Get source schema
            - source_list: List all sources

        Query Operations:
            - query_execute: Execute SQL query
            - query_sample: Sample data from source

        Schema Operations:
            - schema_browse: Browse available schemas
            - schema_inspect: Inspect table schema
    """

    def __init__(self, sbdk_home: Optional[Path] = None):
        """
        Initialize MCP server.

        Args:
            sbdk_home: Optional SBDK home directory
        """
        self.sbdk_home = sbdk_home or Path.home() / ".sbdk"
        self.tools: Dict[str, MCPTool] = {}
        self._initialize_tools()

    def _initialize_tools(self) -> None:
        """Initialize all MCP tools."""
        # Environment tools
        env_tools = EnvironmentTools(sbdk_home=self.sbdk_home)
        self._register_tool(
            "env_create",
            "Create a new SBDK environment",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Environment name (alphanumeric, hyphens, underscores)"
                    },
                    "template": {
                        "type": "string",
                        "enum": ["basic", "analytics", "ml"],
                        "description": "Environment template",
                        "default": "basic"
                    },
                    "target": {
                        "type": "string",
                        "enum": ["duckdb", "postgres", "bigquery"],
                        "description": "Target database",
                        "default": "duckdb"
                    }
                },
                "required": ["name"]
            },
            env_tools.create_environment
        )

        self._register_tool(
            "env_switch",
            "Switch to a different environment",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Environment name to switch to"
                    }
                },
                "required": ["name"]
            },
            env_tools.switch_environment
        )

        self._register_tool(
            "env_list",
            "List all available environments",
            {
                "type": "object",
                "properties": {
                    "verbose": {
                        "type": "boolean",
                        "description": "Include detailed information",
                        "default": False
                    }
                }
            },
            env_tools.list_environments
        )

        self._register_tool(
            "env_status",
            "Get current environment status",
            {
                "type": "object",
                "properties": {
                    "verbose": {
                        "type": "boolean",
                        "description": "Include detailed information",
                        "default": False
                    }
                }
            },
            env_tools.get_status
        )

        # Source tools
        source_tools = SourceTools(sbdk_home=self.sbdk_home)
        self._register_tool(
            "source_add",
            "Add a new data source",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Data source name"
                    },
                    "source_type": {
                        "type": "string",
                        "enum": ["csv", "postgres", "json"],
                        "description": "Type of data source"
                    },
                    "config": {
                        "type": "object",
                        "description": "Source-specific configuration",
                        "properties": {
                            "file_path": {"type": "string"},
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    }
                },
                "required": ["name", "source_type", "config"]
            },
            source_tools.add_source
        )

        self._register_tool(
            "source_test",
            "Test data source connection",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Data source name"
                    }
                },
                "required": ["name"]
            },
            source_tools.test_source
        )

        self._register_tool(
            "source_schema",
            "Get data source schema information",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Data source name"
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Specific table name (optional)"
                    }
                },
                "required": ["name"]
            },
            source_tools.get_schema
        )

        self._register_tool(
            "source_list",
            "List all configured data sources",
            {
                "type": "object",
                "properties": {
                    "verbose": {
                        "type": "boolean",
                        "description": "Include detailed information",
                        "default": False
                    }
                }
            },
            source_tools.list_sources
        )

        # Query tools
        query_tools = QueryTools(sbdk_home=self.sbdk_home)
        self._register_tool(
            "query_execute",
            "Execute SQL query in current environment",
            {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum rows to return",
                        "default": 100
                    }
                },
                "required": ["sql"]
            },
            query_tools.execute_query
        )

        self._register_tool(
            "query_sample",
            "Sample data from a source",
            {
                "type": "object",
                "properties": {
                    "source_name": {
                        "type": "string",
                        "description": "Data source name"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["full", "limit", "percentage", "random"],
                        "description": "Sampling strategy",
                        "default": "limit"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of rows (for limit strategy)",
                        "default": 100
                    },
                    "percentage": {
                        "type": "number",
                        "description": "Percentage to sample (for percentage/random strategy)",
                        "default": 10.0
                    }
                },
                "required": ["source_name"]
            },
            query_tools.sample_data
        )

        # Schema tools
        schema_tools = SchemaTools(sbdk_home=self.sbdk_home)
        self._register_tool(
            "schema_browse",
            "Browse available schemas and tables",
            {
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Environment name (uses current if not specified)"
                    }
                }
            },
            schema_tools.browse_schemas
        )

        self._register_tool(
            "schema_inspect",
            "Inspect detailed table schema",
            {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table name to inspect"
                    },
                    "include_sample": {
                        "type": "boolean",
                        "description": "Include sample data",
                        "default": True
                    }
                },
                "required": ["table_name"]
            },
            schema_tools.inspect_table
        )

        logger.info(f"Initialized {len(self.tools)} MCP tools")

    def _register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ) -> None:
        """Register an MCP tool."""
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )
        self.tools[name] = tool
        logger.debug(f"Registered tool: {name}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.

        Returns:
            List of tool definitions (name, description, parameters)

        Example:
            >>> server = MCPServer()
            >>> tools = server.list_tools()
            >>> for tool in tools:
            ...     print(f"{tool['name']}: {tool['description']}")
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]

    def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """
        Invoke an MCP tool.

        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters as dictionary

        Returns:
            MCPToolResult with success status and data

        Example:
            >>> server = MCPServer()
            >>> result = server.invoke_tool("env_list", {})
            >>> if result.success:
            ...     print(result.data)
        """
        if tool_name not in self.tools:
            return MCPToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}. Available tools: {', '.join(self.tools.keys())}"
            )

        tool = self.tools[tool_name]
        try:
            logger.info(f"Invoking tool: {tool_name} with parameters: {parameters}")
            data = tool.handler(**parameters)
            return MCPToolResult(
                success=True,
                data=data,
                metadata={"tool": tool_name, "parameters": parameters}
            )
        except TypeError as e:
            return MCPToolResult(
                success=False,
                error=f"Invalid parameters for {tool_name}: {e}"
            )
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
            return MCPToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool definition or None if not found
        """
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }

    def export_manifest(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export MCP server manifest (tool definitions for AI agents).

        Args:
            output_path: Optional path to save manifest JSON

        Returns:
            Manifest dictionary

        Example:
            >>> server = MCPServer()
            >>> manifest = server.export_manifest(Path("mcp_manifest.json"))
        """
        manifest = {
            "version": "1.0",
            "server": "sbdk-mcp",
            "description": "SBDK Model Context Protocol Server",
            "tools": self.list_tools()
        }

        if output_path:
            output_path.write_text(json.dumps(manifest, indent=2))
            logger.info(f"Exported manifest to {output_path}")

        return manifest
