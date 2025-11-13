"""
Tests for MCP Tools

Tests all MCP tool implementations:
- EnvironmentTools
- SourceTools
- QueryTools
- SchemaTools
"""

import csv
import json
from pathlib import Path

import pytest

from sbdk.environment import EnvironmentTemplate
from sbdk.mcp.tools import EnvironmentTools, QueryTools, SchemaTools, SourceTools


class TestEnvironmentTools:
    """Test suite for EnvironmentTools."""

    @pytest.fixture
    def env_tools(self, tmp_path):
        """Create EnvironmentTools with temp directory."""
        sbdk_home = tmp_path / ".sbdk"
        return EnvironmentTools(sbdk_home=sbdk_home)

    def test_create_environment_basic(self, env_tools):
        """Test creating basic environment."""
        result = env_tools.create_environment("dev", template="basic", target="duckdb")

        assert result["status"] == "created"
        assert result["name"] == "dev"
        assert "path" in result
        assert result["template"] == "basic"
        assert result["target"] == "duckdb"

        # Verify environment directory exists
        env_path = Path(result["path"])
        assert env_path.exists()
        assert env_path.is_dir()

    def test_create_environment_analytics(self, env_tools):
        """Test creating analytics environment."""
        result = env_tools.create_environment("analytics", template="analytics")

        assert result["status"] == "created"
        assert result["template"] == "analytics"

    def test_create_environment_ml(self, env_tools):
        """Test creating ML environment."""
        result = env_tools.create_environment("ml", template="ml")

        assert result["status"] == "created"
        assert result["template"] == "ml"

    def test_create_environment_invalid_template(self, env_tools):
        """Test creating environment with invalid template."""
        with pytest.raises(ValueError):
            env_tools.create_environment("test", template="invalid")

    def test_create_environment_invalid_name(self, env_tools):
        """Test creating environment with invalid name."""
        with pytest.raises(ValueError):
            env_tools.create_environment("invalid@name")

    def test_create_environment_duplicate(self, env_tools):
        """Test creating duplicate environment."""
        env_tools.create_environment("dev")

        with pytest.raises(ValueError):
            env_tools.create_environment("dev")

    def test_switch_environment(self, env_tools):
        """Test switching between environments."""
        env_tools.create_environment("dev")
        env_tools.create_environment("staging")

        result = env_tools.switch_environment("dev")
        assert result["status"] == "switched"
        assert result["active_environment"] == "dev"

        result = env_tools.switch_environment("staging")
        assert result["active_environment"] == "staging"

    def test_switch_environment_not_exists(self, env_tools):
        """Test switching to non-existent environment."""
        with pytest.raises(ValueError):
            env_tools.switch_environment("nonexistent")

    def test_list_environments(self, env_tools):
        """Test listing environments."""
        # Create multiple environments
        env_tools.create_environment("dev")
        env_tools.create_environment("staging")
        env_tools.create_environment("prod")
        env_tools.switch_environment("dev")

        result = env_tools.list_environments()

        assert "environments" in result
        assert result["total"] == 3
        assert result["active"] == "dev"

        # Check environment structure
        for env in result["environments"]:
            assert "name" in env
            assert "template" in env
            assert "target" in env
            assert "active" in env

        # One should be active
        active_envs = [e for e in result["environments"] if e["active"]]
        assert len(active_envs) == 1
        assert active_envs[0]["name"] == "dev"

    def test_list_environments_empty(self, env_tools):
        """Test listing when no environments exist."""
        result = env_tools.list_environments()

        assert result["total"] == 0
        assert len(result["environments"]) == 0

    def test_get_status(self, env_tools):
        """Test getting environment status."""
        env_tools.create_environment("dev")
        env_tools.switch_environment("dev")

        status = env_tools.get_status()

        assert "active_environment" in status
        assert status["active_environment"] == "dev"
        assert "total_environments" in status


class TestSourceTools:
    """Test suite for SourceTools."""

    @pytest.fixture
    def source_tools(self, tmp_path):
        """Create SourceTools with temp directory."""
        sbdk_home = tmp_path / ".sbdk"
        return SourceTools(sbdk_home=sbdk_home)

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV file."""
        csv_file = tmp_path / "data.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "age"])
            writer.writeheader()
            writer.writerows([
                {"id": "1", "name": "Alice", "age": "30"},
                {"id": "2", "name": "Bob", "age": "25"},
                {"id": "3", "name": "Charlie", "age": "35"},
            ])
        return csv_file

    def test_add_source_csv(self, source_tools, sample_csv):
        """Test adding CSV data source."""
        result = source_tools.add_source(
            "users",
            "csv",
            {"file_path": str(sample_csv)}
        )

        assert result["status"] == "added"
        assert result["name"] == "users"
        assert result["type"] == "csv"

        # Verify config file exists
        config_path = Path(result["config_path"])
        assert config_path.exists()

        # Verify config content
        config = json.loads(config_path.read_text())
        assert config["name"] == "users"
        assert config["type"] == "csv"
        assert config["config"]["file_path"] == str(sample_csv)

    def test_add_source_json(self, source_tools, tmp_path):
        """Test adding JSON data source."""
        json_file = tmp_path / "data.json"
        json_file.write_text('[{"id": 1, "name": "Test"}]')

        result = source_tools.add_source(
            "products",
            "json",
            {"file_path": str(json_file)}
        )

        assert result["status"] == "added"
        assert result["type"] == "json"

    def test_test_source_csv_success(self, source_tools, sample_csv):
        """Test successful CSV source connection test."""
        source_tools.add_source("users", "csv", {"file_path": str(sample_csv)})

        result = source_tools.test_source("users")

        assert result["connected"] is True
        assert result["name"] == "users"
        assert result["type"] == "csv"

    def test_test_source_file_not_found(self, source_tools):
        """Test source connection when file doesn't exist."""
        source_tools.add_source(
            "missing",
            "csv",
            {"file_path": "/nonexistent/file.csv"}
        )

        result = source_tools.test_source("missing")

        assert result["connected"] is False
        assert "error" in result

    def test_test_source_not_exists(self, source_tools):
        """Test testing non-existent source."""
        result = source_tools.test_source("nonexistent")

        assert result["connected"] is False
        assert "error" in result

    def test_get_schema(self, source_tools, sample_csv):
        """Test getting source schema."""
        source_tools.add_source("users", "csv", {"file_path": str(sample_csv)})

        schema = source_tools.get_schema("users")

        assert "table_name" in schema
        assert "columns" in schema
        assert "row_count" in schema

        # Check columns
        assert len(schema["columns"]) == 3
        column_names = [col["name"] for col in schema["columns"]]
        assert "id" in column_names
        assert "name" in column_names
        assert "age" in column_names

    def test_get_schema_source_not_exists(self, source_tools):
        """Test getting schema for non-existent source."""
        with pytest.raises(ValueError):
            source_tools.get_schema("nonexistent")

    def test_list_sources(self, source_tools, sample_csv):
        """Test listing all sources."""
        # Add multiple sources
        source_tools.add_source("users", "csv", {"file_path": str(sample_csv)})
        source_tools.add_source("products", "csv", {"file_path": str(sample_csv)})

        result = source_tools.list_sources()

        assert result["total"] == 2
        assert len(result["sources"]) == 2

        # Check source structure
        for source in result["sources"]:
            assert "name" in source
            assert "type" in source

    def test_list_sources_verbose(self, source_tools, sample_csv):
        """Test listing sources with verbose output."""
        source_tools.add_source("users", "csv", {"file_path": str(sample_csv)})

        result = source_tools.list_sources(verbose=True)

        assert result["total"] == 1
        # Verbose should include config
        assert "config" in result["sources"][0]

    def test_list_sources_empty(self, source_tools):
        """Test listing when no sources exist."""
        result = source_tools.list_sources()

        assert result["total"] == 0
        assert len(result["sources"]) == 0


class TestQueryTools:
    """Test suite for QueryTools."""

    @pytest.fixture
    def query_tools(self, tmp_path):
        """Create QueryTools with temp directory."""
        sbdk_home = tmp_path / ".sbdk"
        return QueryTools(sbdk_home=sbdk_home)

    @pytest.fixture
    def setup_source(self, tmp_path):
        """Setup a test data source."""
        # Create CSV file
        csv_file = tmp_path / "data.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "value"])
            writer.writeheader()
            for i in range(1, 21):
                writer.writerow({"id": str(i), "name": f"Item {i}", "value": str(i * 10)})

        # Create source config
        sources_dir = tmp_path / ".sbdk" / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)

        source_config = {
            "name": "test_data",
            "type": "csv",
            "config": {"file_path": str(csv_file)}
        }
        (sources_dir / "test_data.json").write_text(json.dumps(source_config))

        return tmp_path / ".sbdk"

    def test_execute_query_not_implemented(self, query_tools):
        """Test that query execution returns not implemented message."""
        result = query_tools.execute_query("SELECT * FROM users")

        assert result["status"] == "not_implemented"
        assert "message" in result

    def test_sample_data_limit_strategy(self, query_tools, setup_source, monkeypatch):
        """Test sampling with limit strategy."""
        monkeypatch.setattr(query_tools, "sbdk_home", setup_source)

        result = query_tools.sample_data("test_data", strategy="limit", limit=5)

        assert result["source"] == "test_data"
        assert result["strategy"] == "limit"
        assert result["count"] == 5
        assert len(result["rows"]) == 5

    def test_sample_data_percentage_strategy(self, query_tools, setup_source, monkeypatch):
        """Test sampling with percentage strategy."""
        monkeypatch.setattr(query_tools, "sbdk_home", setup_source)

        result = query_tools.sample_data("test_data", strategy="percentage", percentage=50.0)

        assert result["strategy"] == "percentage"
        assert result["count"] > 0
        # Should be roughly 50% of 20 rows
        assert 5 <= result["count"] <= 15

    def test_sample_data_source_not_found(self, query_tools):
        """Test sampling non-existent source."""
        with pytest.raises(ValueError):
            query_tools.sample_data("nonexistent")


class TestSchemaTools:
    """Test suite for SchemaTools."""

    @pytest.fixture
    def schema_tools(self, tmp_path):
        """Create SchemaTools with temp directory."""
        sbdk_home = tmp_path / ".sbdk"
        return SchemaTools(sbdk_home=sbdk_home)

    @pytest.fixture
    def setup_sources(self, tmp_path):
        """Setup test data sources."""
        # Create CSV files
        csv1 = tmp_path / "users.csv"
        with open(csv1, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name"])
            writer.writeheader()
            writer.writerow({"id": "1", "name": "Alice"})

        csv2 = tmp_path / "products.csv"
        with open(csv2, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "product"])
            writer.writeheader()
            writer.writerow({"id": "1", "product": "Widget"})

        # Create source configs
        sources_dir = tmp_path / ".sbdk" / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)

        for name, file_path in [("users", csv1), ("products", csv2)]:
            config = {
                "name": name,
                "type": "csv",
                "config": {"file_path": str(file_path)}
            }
            (sources_dir / f"{name}.json").write_text(json.dumps(config))

        return tmp_path / ".sbdk"

    def test_browse_schemas(self, schema_tools, setup_sources, monkeypatch):
        """Test browsing available schemas."""
        monkeypatch.setattr(schema_tools.source_tools, "sbdk_home", setup_sources)
        schema_tools.sbdk_home = setup_sources

        result = schema_tools.browse_schemas()

        assert "schemas" in result
        assert result["total"] == 2

        schema_names = [s["name"] for s in result["schemas"]]
        assert "users" in schema_names
        assert "products" in schema_names

    def test_browse_schemas_empty(self, schema_tools):
        """Test browsing when no schemas exist."""
        result = schema_tools.browse_schemas()

        assert result["total"] == 0

    def test_inspect_table(self, schema_tools, setup_sources, monkeypatch):
        """Test inspecting a table."""
        monkeypatch.setattr(schema_tools.source_tools, "sbdk_home", setup_sources)
        schema_tools.sbdk_home = setup_sources

        result = schema_tools.inspect_table("users", include_sample=True)

        assert result["table_name"] == "users"
        assert "schema" in result
        assert "sample" in result

        # Check schema
        assert "columns" in result["schema"]

        # Check sample
        assert isinstance(result["sample"], list)

    def test_inspect_table_no_sample(self, schema_tools, setup_sources, monkeypatch):
        """Test inspecting table without sample."""
        monkeypatch.setattr(schema_tools.source_tools, "sbdk_home", setup_sources)
        schema_tools.sbdk_home = setup_sources

        result = schema_tools.inspect_table("users", include_sample=False)

        assert "schema" in result
        assert "sample" not in result

    def test_inspect_table_not_exists(self, schema_tools):
        """Test inspecting non-existent table."""
        with pytest.raises(ValueError):
            schema_tools.inspect_table("nonexistent")
