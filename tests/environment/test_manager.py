"""
Tests for EnvironmentManager.
"""

import json
from pathlib import Path

import pytest

from sbdk.environment import (
    EnvironmentManager,
    EnvironmentTemplate,
    EnvironmentTarget,
)
from sbdk.exceptions import ValidationError


class TestEnvironmentManager:
    """Test suite for EnvironmentManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create EnvironmentManager with temporary directory."""
        sbdk_home = tmp_path / ".sbdk"
        return EnvironmentManager(sbdk_home=sbdk_home)

    def test_create_environment_basic(self, manager):
        """Test creating a basic environment."""
        env_path = manager.create("dev")

        assert env_path.exists()
        assert (env_path / "config.json").exists()
        assert (env_path / "data").exists()
        assert (env_path / "pipelines").exists()
        assert (env_path / "dbt").exists()

    def test_create_environment_with_template(self, manager):
        """Test creating environment with template."""
        env_path = manager.create(
            "analytics",
            template=EnvironmentTemplate.ANALYTICS
        )

        assert env_path.exists()

        # Load config to verify template was applied
        config_path = env_path / "config.json"
        with open(config_path) as f:
            config_data = json.load(f)

        assert config_data["name"] == "analytics"
        assert config_data["template"] == "analytics"

    def test_create_environment_duplicate_raises_error(self, manager):
        """Test that creating duplicate environment raises error."""
        manager.create("dev")

        with pytest.raises(ValidationError) as exc_info:
            manager.create("dev")

        assert "already exists" in str(exc_info.value).lower()

    def test_list_environments_empty(self, manager):
        """Test listing environments when none exist."""
        environments = manager.list_environments()

        assert environments == []

    def test_list_environments(self, manager):
        """Test listing multiple environments."""
        manager.create("dev", template=EnvironmentTemplate.BASIC)
        manager.create("staging", template=EnvironmentTemplate.ANALYTICS)
        manager.create("prod", template=EnvironmentTemplate.ML)

        environments = manager.list_environments()

        assert len(environments) == 3

        # Verify sorted by name
        names = [env["name"] for env in environments]
        assert names == ["dev", "prod", "staging"]

        # Verify template info
        dev_env = next(e for e in environments if e["name"] == "dev")
        assert dev_env["template"] == "basic"

    def test_switch_environment(self, manager):
        """Test switching between environments."""
        manager.create("dev")
        manager.create("staging")

        # Switch to dev
        manager.switch("dev")
        active = manager.get_active_environment()
        assert active == "dev"

        # Switch to staging
        manager.switch("staging")
        active = manager.get_active_environment()
        assert active == "staging"

    def test_switch_nonexistent_environment_raises_error(self, manager):
        """Test switching to non-existent environment raises error."""
        with pytest.raises(ValidationError) as exc_info:
            manager.switch("nonexistent")

        assert "not found" in str(exc_info.value).lower()

    def test_get_active_environment_none(self, manager):
        """Test getting active environment when none is active."""
        active = manager.get_active_environment()
        assert active is None

    def test_get_environment(self, manager):
        """Test getting environment configuration."""
        manager.create("dev", template=EnvironmentTemplate.ANALYTICS)

        config = manager.get_environment("dev")

        assert config.name == "dev"
        assert config.template == EnvironmentTemplate.ANALYTICS

    def test_get_nonexistent_environment_raises_error(self, manager):
        """Test getting non-existent environment raises error."""
        with pytest.raises(ValidationError) as exc_info:
            manager.get_environment("nonexistent")

        assert "not found" in str(exc_info.value).lower()

    def test_delete_environment(self, manager):
        """Test deleting an environment."""
        env_path = manager.create("dev")
        assert env_path.exists()

        manager.delete("dev", force=True)

        assert not env_path.exists()

    def test_delete_active_environment_without_force_raises_error(self, manager):
        """Test deleting active environment without force raises error."""
        manager.create("dev")
        manager.switch("dev")

        with pytest.raises(ValidationError) as exc_info:
            manager.delete("dev")

        assert "active" in str(exc_info.value).lower()

    def test_delete_active_environment_with_force(self, manager):
        """Test deleting active environment with force flag."""
        env_path = manager.create("dev")
        manager.switch("dev")

        manager.delete("dev", force=True)

        assert not env_path.exists()
        assert manager.get_active_environment() is None

    def test_get_status(self, manager):
        """Test getting environment manager status."""
        manager.create("dev")
        manager.create("staging")
        manager.switch("dev")

        status = manager.get_status()

        assert status["active_environment"] == "dev"
        assert status["total_environments"] == 2
        assert len(status["environments"]) == 2

    def test_create_from_copy(self, manager):
        """Test creating environment by copying existing one."""
        # Create source environment
        manager.create("dev", template=EnvironmentTemplate.ANALYTICS)

        # Copy to new environment
        staging_path = manager.create("staging", copy_from="dev")

        assert staging_path.exists()

        # Verify copied config
        staging_config = manager.get_environment("staging")
        dev_config = manager.get_environment("dev")

        assert staging_config.name == "staging"
        assert staging_config.template == dev_config.template
        assert staging_config.target == dev_config.target
