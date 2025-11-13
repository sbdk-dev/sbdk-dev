"""
SBDK MCP (Model Context Protocol) Server

Provides AI agents access to SBDK capabilities through the Model Context Protocol.
This is the critical integration layer enabling AI-assisted data development.

Example:
    >>> from sbdk.mcp import MCPServer
    >>> server = MCPServer()
    >>> server.run(port=3000)
"""

from sbdk.mcp.server import MCPServer
from sbdk.mcp.tools import (
    EnvironmentTools,
    SourceTools,
    QueryTools,
    SchemaTools,
)

__all__ = [
    "MCPServer",
    "EnvironmentTools",
    "SourceTools",
    "QueryTools",
    "SchemaTools",
]
