"""
Tests for MCP Server Core

Tests the core MCPServer functionality including:
- Tool registration and discovery
- Tool invocation
- Error handling
- Manifest export
"""

import json
from pathlib import Path

import pytest

from sbdk.mcp import MCPServer


class TestMCPServer:
    """Test suite for MCPServer core functionality."""

    @pytest.fixture
    def server(self, tmp_path):
        """Create MCP server with temp home directory."""
        sbdk_home = tmp_path / ".sbdk"
        return MCPServer(sbdk_home=sbdk_home)

    def test_server_initialization(self, server):
        """Test server initializes with tools."""
        assert server is not None
        assert len(server.tools) > 0
        assert server.sbdk_home.exists()

    def test_list_tools(self, server):
        """Test listing all available tools."""
        tools = server.list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert isinstance(tool["name"], str)
            assert isinstance(tool["description"], str)
            assert isinstance(tool["parameters"], dict)

    def test_tool_categories(self, server):
        """Test that all expected tool categories are present."""
        tools = server.list_tools()
        tool_names = [t["name"] for t in tools]

        # Check environment tools
        assert any("env_" in name for name in tool_names)

        # Check source tools
        assert any("source_" in name for name in tool_names)

        # Check query tools
        assert any("query_" in name for name in tool_names)

        # Check schema tools
        assert any("schema_" in name for name in tool_names)

    def test_get_tool_info_exists(self, server):
        """Test getting info for existing tool."""
        tool_info = server.get_tool_info("env_list")

        assert tool_info is not None
        assert tool_info["name"] == "env_list"
        assert "description" in tool_info
        assert "parameters" in tool_info

    def test_get_tool_info_not_exists(self, server):
        """Test getting info for non-existent tool."""
        tool_info = server.get_tool_info("nonexistent_tool")
        assert tool_info is None

    def test_invoke_tool_success(self, server):
        """Test successful tool invocation."""
        # env_status should always work
        result = server.invoke_tool("env_status", {"verbose": False})

        assert result.success is True
        assert result.data is not None
        assert result.error is None
        assert "tool" in result.metadata

    def test_invoke_tool_unknown(self, server):
        """Test invoking unknown tool."""
        result = server.invoke_tool("unknown_tool", {})

        assert result.success is False
        assert result.error is not None
        assert "Unknown tool" in result.error

    def test_invoke_tool_invalid_parameters(self, server):
        """Test invoking tool with invalid parameters."""
        # env_create requires 'name' parameter
        result = server.invoke_tool("env_create", {"invalid_param": "value"})

        assert result.success is False
        assert result.error is not None

    def test_export_manifest(self, server, tmp_path):
        """Test exporting MCP manifest."""
        output_path = tmp_path / "manifest.json"
        manifest = server.export_manifest(output_path=output_path)

        # Check manifest structure
        assert "version" in manifest
        assert "server" in manifest
        assert "description" in manifest
        assert "tools" in manifest
        assert len(manifest["tools"]) > 0

        # Check file was created
        assert output_path.exists()
        saved_manifest = json.loads(output_path.read_text())
        assert saved_manifest == manifest

    def test_export_manifest_no_file(self, server):
        """Test exporting manifest without saving to file."""
        manifest = server.export_manifest()

        assert "version" in manifest
        assert "tools" in manifest

    def test_tool_parameters_schema(self, server):
        """Test that tool parameters follow JSON Schema format."""
        tools = server.list_tools()

        for tool in tools:
            params = tool["parameters"]

            # Should have type field
            assert "type" in params

            # If it's an object, should have properties
            if params["type"] == "object":
                if "properties" in params:
                    for prop_name, prop_spec in params["properties"].items():
                        assert "type" in prop_spec
                        # Description is optional but recommended
                        if "description" in prop_spec:
                            assert isinstance(prop_spec["description"], str)

    def test_environment_tools_available(self, server):
        """Test that all environment management tools are available."""
        tools = server.list_tools()
        tool_names = [t["name"] for t in tools]

        expected_tools = ["env_create", "env_switch", "env_list", "env_status"]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_source_tools_available(self, server):
        """Test that all source management tools are available."""
        tools = server.list_tools()
        tool_names = [t["name"] for t in tools]

        expected_tools = ["source_add", "source_test", "source_schema", "source_list"]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_query_tools_available(self, server):
        """Test that all query tools are available."""
        tools = server.list_tools()
        tool_names = [t["name"] for t in tools]

        expected_tools = ["query_execute", "query_sample"]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_schema_tools_available(self, server):
        """Test that all schema tools are available."""
        tools = server.list_tools()
        tool_names = [t["name"] for t in tools]

        expected_tools = ["schema_browse", "schema_inspect"]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_tool_descriptions_present(self, server):
        """Test that all tools have meaningful descriptions."""
        tools = server.list_tools()

        for tool in tools:
            assert len(tool["description"]) > 10, f"Tool {tool['name']} has insufficient description"
            # Description should not just be the name
            assert tool["name"] not in tool["description"].lower()

    def test_required_parameters_marked(self, server):
        """Test that required parameters are properly marked."""
        tool_info = server.get_tool_info("env_create")

        assert tool_info is not None
        params = tool_info["parameters"]

        # env_create requires 'name' parameter
        assert "required" in params
        assert "name" in params["required"]

    def test_optional_parameters_have_defaults(self, server):
        """Test that optional parameters have sensible defaults."""
        tool_info = server.get_tool_info("env_create")

        assert tool_info is not None
        params = tool_info["parameters"]["properties"]

        # template and target are optional with defaults
        if "template" in params:
            assert "default" in params["template"] or "template" in tool_info["parameters"].get("required", [])

    def test_enum_parameters_defined(self, server):
        """Test that enum parameters list valid values."""
        tool_info = server.get_tool_info("env_create")

        assert tool_info is not None
        params = tool_info["parameters"]["properties"]

        # template should be an enum
        if "template" in params:
            assert "enum" in params["template"]
            assert len(params["template"]["enum"]) > 0
