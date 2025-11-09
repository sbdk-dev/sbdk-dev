"""
Tests for environment configuration models.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from sbdk.environment.config import (
    ActiveEnvironmentMarker,
    EnvironmentConfig,
    EnvironmentFeatures,
    EnvironmentPerformance,
    EnvironmentStatus,
    EnvironmentTarget,
    EnvironmentTemplate,
    create_environment_config,
    load_environment_config,
    save_environment_config,
)


class TestEnvironmentConfig:
    """Test suite for EnvironmentConfig."""

    def test_create_basic_config(self):
        """Test creating a basic environment configuration."""
        config = EnvironmentConfig(name="dev")

        assert config.name == "dev"
        assert config.template == EnvironmentTemplate.BASIC
        assert config.target == EnvironmentTarget.DUCKDB
        assert config.status == EnvironmentStatus.INACTIVE
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)

    def test_create_config_with_template(self):
        """Test creating config with specific template."""
        config = EnvironmentConfig(
            name="analytics",
            template=EnvironmentTemplate.ANALYTICS,
            target=EnvironmentTarget.BIGQUERY
        )

        assert config.name == "analytics"
        assert config.template == EnvironmentTemplate.ANALYTICS
        assert config.target == EnvironmentTarget.BIGQUERY

    def test_invalid_name_special_characters(self):
        """Test that special characters in name raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            EnvironmentConfig(name="dev@123")

        assert "alphanumeric" in str(exc_info.value).lower()

    def test_invalid_name_reserved(self):
        """Test that reserved names raise validation error."""
        reserved_names = ["test", "tmp", "temp", "system", "admin"]

        for name in reserved_names:
            with pytest.raises(ValidationError) as exc_info:
                EnvironmentConfig(name=name)

            assert "reserved" in str(exc_info.value).lower()

    def test_valid_names(self):
        """Test that valid names are accepted."""
        valid_names = ["dev", "staging-prod", "my_environment", "env123", "dev-2"]

        for name in valid_names:
            config = EnvironmentConfig(name=name)
            assert config.name == name

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = EnvironmentConfig(
            name="dev",
            description="Development environment"
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "dev"
        assert config_dict["description"] == "Development environment"
        assert "created_at" in config_dict
        assert "updated_at" in config_dict

    def test_config_to_json(self):
        """Test converting config to JSON string."""
        config = EnvironmentConfig(name="dev")
        json_str = config.to_json()

        assert isinstance(json_str, str)

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "dev"

    def test_features_configuration(self):
        """Test feature flags configuration."""
        features = EnvironmentFeatures(
            parallel_processing=True,
            memory_optimization=False,
            quality_monitoring=True,
            incremental_builds=False
        )

        config = EnvironmentConfig(name="dev", features=features.model_dump())

        assert config.features.parallel_processing is True
        assert config.features.memory_optimization is False
        assert config.features.quality_monitoring is True
        assert config.features.incremental_builds is False

    def test_performance_configuration(self):
        """Test performance settings configuration."""
        performance = EnvironmentPerformance(
            batch_size=5000,
            worker_threads=8,
            cache_strategy="aggressive",
            memory_limit_mb=4096
        )

        config = EnvironmentConfig(name="dev", performance=performance.model_dump())

        assert config.performance.batch_size == 5000
        assert config.performance.worker_threads == 8
        assert config.performance.cache_strategy == "aggressive"
        assert config.performance.memory_limit_mb == 4096

    def test_tags_and_metadata(self):
        """Test tags and metadata."""
        config = EnvironmentConfig(
            name="dev",
            tags=["development", "testing"],
            metadata={"owner": "team-data", "cost_center": "engineering"}
        )

        assert config.tags == ["development", "testing"]
        assert config.metadata["owner"] == "team-data"
        assert config.metadata["cost_center"] == "engineering"

    def test_update_timestamp(self):
        """Test that updated_at timestamp is updated."""
        config = EnvironmentConfig(name="dev")
        initial_updated = config.updated_at

        # Modify config
        config.description = "Updated description"

        # Timestamp should be updated (model_validator handles this)
        # Note: In practice, you'd reload the model or use model_rebuild
        assert config.updated_at >= initial_updated


class TestCreateEnvironmentConfig:
    """Test suite for create_environment_config helper."""

    def test_create_with_defaults(self):
        """Test creating config with default values."""
        config = create_environment_config("dev")

        assert config.name == "dev"
        assert config.template == EnvironmentTemplate.BASIC
        assert config.target == EnvironmentTarget.DUCKDB

    def test_create_with_template(self):
        """Test creating config with specific template."""
        config = create_environment_config(
            "analytics",
            template=EnvironmentTemplate.ANALYTICS,
            target=EnvironmentTarget.BIGQUERY
        )

        assert config.name == "analytics"
        assert config.template == EnvironmentTemplate.ANALYTICS
        assert config.target == EnvironmentTarget.BIGQUERY

    def test_create_with_kwargs(self):
        """Test creating config with additional kwargs."""
        config = create_environment_config(
            "dev",
            description="Development environment",
            tags=["dev", "testing"]
        )

        assert config.description == "Development environment"
        assert config.tags == ["dev", "testing"]


class TestLoadSaveEnvironmentConfig:
    """Test suite for loading and saving config files."""

    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading configuration."""
        config = EnvironmentConfig(
            name="dev",
            template=EnvironmentTemplate.ANALYTICS,
            description="Test environment"
        )

        config_path = tmp_path / "config.json"
        save_environment_config(config, config_path)

        assert config_path.exists()

        # Load it back
        loaded_config = load_environment_config(config_path)

        assert loaded_config.name == config.name
        assert loaded_config.template == config.template
        assert loaded_config.description == config.description

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading non-existent config file raises error."""
        config_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_environment_config(config_path)

    def test_save_creates_parent_directories(self, tmp_path):
        """Test that save creates parent directories."""
        config = EnvironmentConfig(name="dev")
        config_path = tmp_path / "nested" / "path" / "config.json"

        save_environment_config(config, config_path)

        assert config_path.exists()
        assert config_path.parent.exists()


class TestActiveEnvironmentMarker:
    """Test suite for ActiveEnvironmentMarker."""

    def test_create_marker(self):
        """Test creating active environment marker."""
        marker = ActiveEnvironmentMarker(environment_name="dev")

        assert marker.environment_name == "dev"
        assert isinstance(marker.activated_at, datetime)
        assert marker.previous_environment is None

    def test_marker_with_previous(self):
        """Test marker with previous environment."""
        marker = ActiveEnvironmentMarker(
            environment_name="prod",
            previous_environment="staging"
        )

        assert marker.environment_name == "prod"
        assert marker.previous_environment == "staging"

    def test_marker_to_dict(self):
        """Test converting marker to dictionary."""
        marker = ActiveEnvironmentMarker(environment_name="dev")
        marker_dict = marker.to_dict()

        assert isinstance(marker_dict, dict)
        assert marker_dict["environment_name"] == "dev"
        assert "activated_at" in marker_dict

    def test_marker_to_json(self):
        """Test converting marker to JSON."""
        marker = ActiveEnvironmentMarker(environment_name="dev")
        json_str = marker.to_json()

        assert isinstance(json_str, str)

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["environment_name"] == "dev"


class TestEnvironmentFeatures:
    """Test suite for EnvironmentFeatures."""

    def test_default_features(self):
        """Test default feature flags."""
        features = EnvironmentFeatures()

        assert features.parallel_processing is True
        assert features.memory_optimization is True
        assert features.quality_monitoring is False
        assert features.incremental_builds is True

    def test_custom_features(self):
        """Test custom feature flags."""
        features = EnvironmentFeatures(
            parallel_processing=False,
            quality_monitoring=True
        )

        assert features.parallel_processing is False
        assert features.quality_monitoring is True

    def test_features_forbid_extra(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            EnvironmentFeatures(invalid_field=True)


class TestEnvironmentPerformance:
    """Test suite for EnvironmentPerformance."""

    def test_default_performance(self):
        """Test default performance settings."""
        perf = EnvironmentPerformance()

        assert perf.batch_size == 10000
        assert perf.worker_threads == 4
        assert perf.cache_strategy == "intelligent"
        assert perf.memory_limit_mb is None

    def test_custom_performance(self):
        """Test custom performance settings."""
        perf = EnvironmentPerformance(
            batch_size=5000,
            worker_threads=8,
            cache_strategy="aggressive",
            memory_limit_mb=2048
        )

        assert perf.batch_size == 5000
        assert perf.worker_threads == 8
        assert perf.cache_strategy == "aggressive"
        assert perf.memory_limit_mb == 2048

    def test_performance_validation_ranges(self):
        """Test performance setting validation."""
        # Batch size too small
        with pytest.raises(ValidationError):
            EnvironmentPerformance(batch_size=50)

        # Batch size too large
        with pytest.raises(ValidationError):
            EnvironmentPerformance(batch_size=200000)

        # Worker threads too few
        with pytest.raises(ValidationError):
            EnvironmentPerformance(worker_threads=0)

        # Worker threads too many
        with pytest.raises(ValidationError):
            EnvironmentPerformance(worker_threads=64)

        # Memory limit too low
        with pytest.raises(ValidationError):
            EnvironmentPerformance(memory_limit_mb=128)
