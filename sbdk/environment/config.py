"""
Environment Configuration Models

Pydantic models for SBDK environment configuration with validation.
Supports multiple environment types (dev, staging, prod) with templates.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class EnvironmentTarget(str, Enum):
    """Target database for environment."""

    DUCKDB = "duckdb"
    POSTGRES = "postgres"
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"


class EnvironmentTemplate(str, Enum):
    """Pre-defined environment templates."""

    ANALYTICS = "analytics"
    ML = "ml"
    BASIC = "basic"
    CUSTOM = "custom"


class EnvironmentStatus(str, Enum):
    """Environment status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class EnvironmentFeatures(BaseModel):
    """Feature flags for environment."""

    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    memory_optimization: bool = Field(default=True, description="Enable memory optimization")
    quality_monitoring: bool = Field(default=False, description="Enable quality monitoring")
    incremental_builds: bool = Field(default=True, description="Enable incremental builds")

    class Config:
        """Pydantic configuration."""
        extra = "forbid"


class EnvironmentPerformance(BaseModel):
    """Performance settings for environment."""

    batch_size: int = Field(default=10000, ge=100, le=100000, description="Batch size for processing")
    worker_threads: int = Field(default=4, ge=1, le=32, description="Number of worker threads")
    cache_strategy: str = Field(default="intelligent", description="Cache strategy")
    memory_limit_mb: Optional[int] = Field(default=None, ge=256, description="Memory limit in MB")

    class Config:
        """Pydantic configuration."""
        extra = "forbid"


class EnvironmentConfig(BaseModel):
    """
    Environment configuration with validation.

    Represents a single SBDK environment (e.g., dev, staging, prod) with
    all necessary configuration for isolated execution.

    Example:
        >>> config = EnvironmentConfig(
        ...     name="dev",
        ...     template=EnvironmentTemplate.ANALYTICS,
        ...     target=EnvironmentTarget.DUCKDB
        ... )
        >>> print(config.name)
        dev
    """

    # Core settings
    name: str = Field(..., min_length=1, max_length=64, description="Environment name")
    template: EnvironmentTemplate = Field(default=EnvironmentTemplate.BASIC, description="Template used")
    target: EnvironmentTarget = Field(default=EnvironmentTarget.DUCKDB, description="Target database")
    description: Optional[str] = Field(default=None, max_length=256, description="Environment description")

    # Status and metadata
    status: EnvironmentStatus = Field(default=EnvironmentStatus.INACTIVE, description="Environment status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Paths (relative to environment directory)
    duckdb_path: str = Field(default="data/sandbox.duckdb", description="DuckDB file path")
    pipelines_path: str = Field(default="pipelines", description="Pipelines directory")
    dbt_path: str = Field(default="dbt", description="dbt project directory")
    profiles_dir: str = Field(default="~/.dbt", description="dbt profiles directory")

    # Features and performance
    features: EnvironmentFeatures = Field(default_factory=EnvironmentFeatures, description="Feature flags")
    performance: EnvironmentPerformance = Field(default_factory=EnvironmentPerformance, description="Performance settings")

    # Custom metadata
    tags: List[str] = Field(default_factory=list, description="Environment tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate environment name.

        Args:
            v: Environment name

        Returns:
            Validated name

        Raises:
            ValueError: If name is invalid
        """
        # Allow alphanumeric, hyphens, and underscores
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Environment name must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )

        # Reserved names
        reserved = ["test", "tmp", "temp", "system", "admin"]
        if v.lower() in reserved:
            raise ValueError(f"Environment name '{v}' is reserved")

        return v

    @model_validator(mode="after")
    def update_timestamp(self) -> "EnvironmentConfig":
        """Update the updated_at timestamp on modification."""
        self.updated_at = datetime.utcnow()
        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary.

        Returns:
            Dictionary representation
        """
        return self.model_dump(mode="json")

    def to_json(self, indent: int = 2) -> str:
        """
        Convert config to JSON string.

        Args:
            indent: JSON indentation

        Returns:
            JSON string
        """
        return self.model_dump_json(indent=indent)

    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v)
        }


class ActiveEnvironmentMarker(BaseModel):
    """
    Marker for the currently active environment.

    Stored in .sbdk/active-environment to track which environment
    is currently being used.
    """

    environment_name: str = Field(..., description="Name of active environment")
    activated_at: datetime = Field(default_factory=datetime.utcnow, description="Activation timestamp")
    previous_environment: Optional[str] = Field(default=None, description="Previous environment name")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode="json")

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=indent)

    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def create_environment_config(
    name: str,
    template: EnvironmentTemplate = EnvironmentTemplate.BASIC,
    target: EnvironmentTarget = EnvironmentTarget.DUCKDB,
    **kwargs: Any
) -> EnvironmentConfig:
    """
    Create a new environment configuration.

    Args:
        name: Environment name
        template: Template to use
        target: Target database
        **kwargs: Additional configuration options

    Returns:
        EnvironmentConfig instance

    Example:
        >>> config = create_environment_config("dev", template=EnvironmentTemplate.ANALYTICS)
        >>> config.name
        'dev'
    """
    return EnvironmentConfig(
        name=name,
        template=template,
        target=target,
        **kwargs
    )


def load_environment_config(config_path: Path) -> EnvironmentConfig:
    """
    Load environment configuration from JSON file.

    Args:
        config_path: Path to config.json file

    Returns:
        Loaded EnvironmentConfig

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
    """
    import json

    if not config_path.exists():
        raise FileNotFoundError(f"Environment config not found: {config_path}")

    with open(config_path) as f:
        data = json.load(f)

    return EnvironmentConfig(**data)


def save_environment_config(config: EnvironmentConfig, config_path: Path) -> None:
    """
    Save environment configuration to JSON file.

    Args:
        config: Environment configuration
        config_path: Path to save config.json

    Raises:
        IOError: If save operation fails
    """
    import json

    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)
