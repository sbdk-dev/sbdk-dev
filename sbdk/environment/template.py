"""
Environment Template Engine

Provides template-based environment creation with pre-configured
settings for different use cases (analytics, ML, basic).
"""

import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from sbdk.environment.config import (
    EnvironmentConfig,
    EnvironmentFeatures,
    EnvironmentPerformance,
    EnvironmentTarget,
    EnvironmentTemplate,
    create_environment_config,
)
from sbdk.exceptions import TemplateError, ValidationError


class TemplateEngine:
    """
    Environment template engine.

    Creates environments from pre-defined templates or custom configurations.

    Example:
        >>> engine = TemplateEngine()
        >>> config = engine.create_from_template("dev", EnvironmentTemplate.ANALYTICS)
        >>> config.features.quality_monitoring
        True
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template engine.

        Args:
            templates_dir: Directory containing template files (optional)
        """
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"

    def create_from_template(
        self,
        name: str,
        template: EnvironmentTemplate,
        target: EnvironmentTarget = EnvironmentTarget.DUCKDB,
        **overrides: Any
    ) -> EnvironmentConfig:
        """
        Create environment configuration from template.

        Args:
            name: Environment name
            template: Template to use
            target: Target database
            **overrides: Configuration overrides

        Returns:
            Configured EnvironmentConfig

        Raises:
            ValidationError: If template is invalid

        Example:
            >>> engine = TemplateEngine()
            >>> config = engine.create_from_template("dev", EnvironmentTemplate.ANALYTICS)
        """
        # Get template-specific configuration
        template_config = self._get_template_config(template)

        # Merge with overrides
        template_config.update(overrides)

        # Create config
        return create_environment_config(
            name=name,
            template=template,
            target=target,
            **template_config
        )

    def copy_template_files(
        self,
        template: EnvironmentTemplate,
        destination: Path
    ) -> None:
        """
        Copy template files to environment directory.

        Args:
            template: Template to copy
            destination: Destination directory

        Raises:
            TemplateError: If template files are missing or copy fails
        """
        if template == EnvironmentTemplate.CUSTOM:
            # Custom templates don't have pre-defined files
            return

        template_source = self.templates_dir / template.value

        if not template_source.exists():
            raise TemplateError(
                f"Template files not found: {template_source}",
                suggestion=f"Ensure template '{template.value}' is properly installed"
            )

        try:
            # Create destination if it doesn't exist
            destination.mkdir(parents=True, exist_ok=True)

            # Copy template files
            for item in template_source.iterdir():
                if item.is_file():
                    shutil.copy2(item, destination / item.name)
                elif item.is_dir():
                    shutil.copytree(item, destination / item.name, dirs_exist_ok=True)

        except (OSError, shutil.Error) as e:
            raise TemplateError(
                f"Failed to copy template files: {e}",
                suggestion="Check file permissions and disk space"
            ) from e

    def create_from_existing(
        self,
        name: str,
        source_config: EnvironmentConfig
    ) -> EnvironmentConfig:
        """
        Create environment configuration by copying existing environment.

        Args:
            name: New environment name
            source_config: Source environment configuration

        Returns:
            New EnvironmentConfig with copied settings

        Example:
            >>> source = engine.create_from_template("dev", EnvironmentTemplate.ANALYTICS)
            >>> staging = engine.create_from_existing("staging", source)
        """
        # Create new config with same template and settings
        config_dict = source_config.to_dict()

        # Update name and reset timestamps
        config_dict["name"] = name
        config_dict.pop("created_at", None)
        config_dict.pop("updated_at", None)

        return EnvironmentConfig(**config_dict)

    def _get_template_config(self, template: EnvironmentTemplate) -> Dict[str, Any]:
        """
        Get template-specific configuration.

        Args:
            template: Template type

        Returns:
            Configuration dictionary for template
        """
        if template == EnvironmentTemplate.ANALYTICS:
            return self._analytics_template()
        elif template == EnvironmentTemplate.ML:
            return self._ml_template()
        elif template == EnvironmentTemplate.BASIC:
            return self._basic_template()
        elif template == EnvironmentTemplate.CUSTOM:
            return {}
        else:
            raise ValidationError(
                f"Unknown template: {template}",
                suggestion="Use 'analytics', 'ml', or 'basic' template"
            )

    def _analytics_template(self) -> Dict[str, Any]:
        """
        Analytics template configuration.

        Optimized for data analytics pipelines with dbt, DLT, and quality monitoring.
        """
        return {
            "description": "Full-featured analytics environment with dbt, DLT, and quality monitoring",
            "features": EnvironmentFeatures(
                parallel_processing=True,
                memory_optimization=True,
                quality_monitoring=True,
                incremental_builds=True,
            ).model_dump(),
            "performance": EnvironmentPerformance(
                batch_size=10000,
                worker_threads=4,
                cache_strategy="intelligent",
                memory_limit_mb=2048,
            ).model_dump(),
            "tags": ["analytics", "production-ready", "dbt", "dlt"],
        }

    def _ml_template(self) -> Dict[str, Any]:
        """
        Machine Learning template configuration.

        Optimized for ML workflows with higher memory limits and performance tuning.
        """
        return {
            "description": "Machine learning environment with optimized performance settings",
            "features": EnvironmentFeatures(
                parallel_processing=True,
                memory_optimization=True,
                quality_monitoring=False,  # Focus on model training
                incremental_builds=True,
            ).model_dump(),
            "performance": EnvironmentPerformance(
                batch_size=5000,  # Smaller batches for ML
                worker_threads=8,  # More threads for parallel training
                cache_strategy="aggressive",
                memory_limit_mb=4096,  # Higher memory for ML
            ).model_dump(),
            "tags": ["ml", "machine-learning", "training"],
        }

    def _basic_template(self) -> Dict[str, Any]:
        """
        Basic template configuration.

        Minimal configuration for simple use cases and experimentation.
        """
        return {
            "description": "Basic environment with minimal configuration",
            "features": EnvironmentFeatures(
                parallel_processing=False,
                memory_optimization=False,
                quality_monitoring=False,
                incremental_builds=False,
            ).model_dump(),
            "performance": EnvironmentPerformance(
                batch_size=10000,
                worker_threads=1,
                cache_strategy="simple",
                memory_limit_mb=512,
            ).model_dump(),
            "tags": ["basic", "minimal", "experimental"],
        }

    def list_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available templates with their descriptions.

        Returns:
            Dictionary mapping template names to their configurations

        Example:
            >>> engine = TemplateEngine()
            >>> templates = engine.list_available_templates()
            >>> print(templates["analytics"]["description"])
        """
        return {
            "analytics": {
                "name": "analytics",
                "description": "Full-featured analytics environment with dbt, DLT, and quality monitoring",
                "features": ["parallel processing", "memory optimization", "quality monitoring", "incremental builds"],
                "use_cases": ["Data analytics", "BI pipelines", "Production data workflows"],
            },
            "ml": {
                "name": "ml",
                "description": "Machine learning environment with optimized performance",
                "features": ["parallel processing", "memory optimization", "high memory limit", "aggressive caching"],
                "use_cases": ["Model training", "Feature engineering", "ML experimentation"],
            },
            "basic": {
                "name": "basic",
                "description": "Basic environment with minimal configuration",
                "features": ["simple setup", "low resource usage"],
                "use_cases": ["Learning", "Quick experiments", "Simple pipelines"],
            },
        }


def create_template_engine(templates_dir: Optional[Path] = None) -> TemplateEngine:
    """
    Create a template engine instance.

    Args:
        templates_dir: Optional custom templates directory

    Returns:
        TemplateEngine instance

    Example:
        >>> engine = create_template_engine()
        >>> config = engine.create_from_template("dev", EnvironmentTemplate.ANALYTICS)
    """
    return TemplateEngine(templates_dir=templates_dir)
