"""
Environment Manager

Main interface for managing SBDK environments.
Handles creation, switching, listing, and deletion of environments.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sbdk.environment.config import (
    ActiveEnvironmentMarker,
    EnvironmentConfig,
    EnvironmentStatus,
    EnvironmentTarget,
    EnvironmentTemplate,
    load_environment_config,
    save_environment_config,
)
from sbdk.environment.template import TemplateEngine
from sbdk.exceptions import ConfigurationError, FileSystemError, ValidationError


class EnvironmentManager:
    """
    SBDK Environment Manager.

    Manages multiple isolated environments with quick switching capability.

    Example:
        >>> manager = EnvironmentManager()
        >>> env_path = manager.create("dev", template=EnvironmentTemplate.ANALYTICS)
        >>> manager.switch("dev")
        >>> environments = manager.list_environments()
    """

    def __init__(self, sbdk_home: Optional[Path] = None):
        """
        Initialize environment manager.

        Args:
            sbdk_home: SBDK home directory (default: ~/.sbdk)
        """
        self.sbdk_home = sbdk_home or Path.home() / ".sbdk"
        self.environments_dir = self.sbdk_home / "environments"
        self.active_marker_path = self.sbdk_home / "active-environment.json"

        # Ensure directories exist
        self.environments_dir.mkdir(parents=True, exist_ok=True)

        # Initialize template engine
        self.template_engine = TemplateEngine()

    def create(
        self,
        name: str,
        template: EnvironmentTemplate = EnvironmentTemplate.BASIC,
        target: EnvironmentTarget = EnvironmentTarget.DUCKDB,
        copy_from: Optional[str] = None,
        **kwargs: Any
    ) -> Path:
        """
        Create a new environment.

        Args:
            name: Environment name
            template: Template to use (if copy_from is None)
            target: Target database
            copy_from: Name of existing environment to copy (optional)
            **kwargs: Additional configuration options

        Returns:
            Path to created environment directory

        Raises:
            ValidationError: If environment already exists or invalid name
            TemplateError: If template creation fails

        Example:
            >>> manager = EnvironmentManager()
            >>> env_path = manager.create("dev", template=EnvironmentTemplate.ANALYTICS)
            >>> print(env_path)
            /home/user/.sbdk/environments/dev
        """
        env_dir = self.environments_dir / name

        # Check if environment already exists
        if env_dir.exists():
            raise ValidationError(
                f"Environment '{name}' already exists",
                suggestion=f"Use a different name or delete existing: sbdk env delete {name}"
            )

        try:
            # Create environment directory
            env_dir.mkdir(parents=True, exist_ok=True)

            # Create configuration
            if copy_from:
                # Copy from existing environment
                source_env = self.get_environment(copy_from)
                config = self.template_engine.create_from_existing(name, source_env)
            else:
                # Create from template
                config = self.template_engine.create_from_template(
                    name=name,
                    template=template,
                    target=target,
                    **kwargs
                )

            # Save configuration
            config_path = env_dir / "config.json"
            save_environment_config(config, config_path)

            # Copy template files (if not copying from existing)
            if not copy_from and template != EnvironmentTemplate.CUSTOM:
                try:
                    self.template_engine.copy_template_files(template, env_dir)
                except Exception:
                    # Template files are optional, don't fail if missing
                    pass

            # Create environment subdirectories
            self._create_environment_structure(env_dir, config)

            return env_dir

        except Exception as e:
            # Clean up on failure
            if env_dir.exists():
                shutil.rmtree(env_dir)
            raise

    def switch(self, name: str) -> None:
        """
        Switch to a different environment.

        Updates the active environment marker and validates the environment exists.

        Args:
            name: Environment name to switch to

        Raises:
            ValidationError: If environment doesn't exist

        Example:
            >>> manager = EnvironmentManager()
            >>> manager.switch("dev")
        """
        # Verify environment exists
        env_dir = self.environments_dir / name
        if not env_dir.exists():
            raise ValidationError(
                f"Environment '{name}' not found",
                suggestion=f"Create it first: sbdk env create {name}"
            )

        # Load environment config to verify it's valid
        config_path = env_dir / "config.json"
        try:
            config = load_environment_config(config_path)
        except Exception as e:
            raise ValidationError(
                f"Invalid environment configuration: {e}",
                suggestion=f"Recreate environment: sbdk env delete {name} && sbdk env create {name}"
            ) from e

        # Get current active environment
        current_active = self.get_active_environment()

        # Update status
        if current_active:
            # Mark current as inactive
            current_config = self.get_environment(current_active)
            current_config.status = EnvironmentStatus.INACTIVE
            self._save_config(current_active, current_config)

        # Mark new as active
        config.status = EnvironmentStatus.ACTIVE
        self._save_config(name, config)

        # Update active marker
        marker = ActiveEnvironmentMarker(
            environment_name=name,
            activated_at=datetime.utcnow(),
            previous_environment=current_active
        )

        with open(self.active_marker_path, "w") as f:
            json.dump(marker.to_dict(), f, indent=2)

    def list_environments(self) -> List[Dict[str, Any]]:
        """
        List all environments with their status.

        Returns:
            List of environment information dictionaries

        Example:
            >>> manager = EnvironmentManager()
            >>> environments = manager.list_environments()
            >>> for env in environments:
            ...     print(f"{env['name']}: {env['status']}")
        """
        environments = []
        active_env = self.get_active_environment()

        if not self.environments_dir.exists():
            return environments

        for env_dir in self.environments_dir.iterdir():
            if not env_dir.is_dir():
                continue

            config_path = env_dir / "config.json"
            if not config_path.exists():
                continue

            try:
                config = load_environment_config(config_path)

                env_info = {
                    "name": config.name,
                    "template": config.template.value,
                    "target": config.target.value,
                    "status": config.status.value,
                    "is_active": config.name == active_env,
                    "created_at": config.created_at.isoformat(),
                    "description": config.description,
                    "tags": config.tags,
                }

                environments.append(env_info)

            except Exception:
                # Skip invalid environments
                continue

        # Sort by name
        environments.sort(key=lambda x: x["name"])

        return environments

    def delete(self, name: str, force: bool = False) -> None:
        """
        Delete an environment.

        Args:
            name: Environment name to delete
            force: Skip confirmation if True

        Raises:
            ValidationError: If environment doesn't exist or is active

        Example:
            >>> manager = EnvironmentManager()
            >>> manager.delete("old-env", force=True)
        """
        env_dir = self.environments_dir / name

        if not env_dir.exists():
            raise ValidationError(
                f"Environment '{name}' not found",
                suggestion="Use 'sbdk env list' to see available environments"
            )

        # Prevent deleting active environment
        active_env = self.get_active_environment()
        if name == active_env and not force:
            raise ValidationError(
                f"Cannot delete active environment '{name}'",
                suggestion=f"Switch to different environment first: sbdk env switch <other-env>"
            )

        try:
            shutil.rmtree(env_dir)

            # Clear active marker if deleting active environment
            if name == active_env:
                self.active_marker_path.unlink(missing_ok=True)

        except OSError as e:
            raise FileSystemError(
                f"Failed to delete environment: {e}",
                suggestion="Check file permissions"
            ) from e

    def get_environment(self, name: str) -> EnvironmentConfig:
        """
        Get environment configuration.

        Args:
            name: Environment name

        Returns:
            EnvironmentConfig for the environment

        Raises:
            ValidationError: If environment doesn't exist
        """
        env_dir = self.environments_dir / name
        config_path = env_dir / "config.json"

        if not config_path.exists():
            raise ValidationError(
                f"Environment '{name}' not found",
                suggestion="Use 'sbdk env list' to see available environments"
            )

        return load_environment_config(config_path)

    def get_active_environment(self) -> Optional[str]:
        """
        Get the name of the currently active environment.

        Returns:
            Active environment name or None if no environment is active
        """
        if not self.active_marker_path.exists():
            return None

        try:
            with open(self.active_marker_path) as f:
                data = json.load(f)
                marker = ActiveEnvironmentMarker(**data)
                return marker.environment_name
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get environment manager status.

        Returns:
            Dictionary with status information

        Example:
            >>> manager = EnvironmentManager()
            >>> status = manager.get_status()
            >>> print(status["active_environment"])
        """
        active_env = self.get_active_environment()
        environments = self.list_environments()

        status = {
            "sbdk_home": str(self.sbdk_home),
            "environments_dir": str(self.environments_dir),
            "active_environment": active_env,
            "total_environments": len(environments),
            "environments": environments,
        }

        if active_env:
            try:
                active_config = self.get_environment(active_env)
                status["active_config"] = {
                    "name": active_config.name,
                    "template": active_config.template.value,
                    "target": active_config.target.value,
                    "description": active_config.description,
                }
            except Exception:
                pass

        return status

    def _create_environment_structure(
        self,
        env_dir: Path,
        config: EnvironmentConfig
    ) -> None:
        """
        Create environment directory structure.

        Args:
            env_dir: Environment root directory
            config: Environment configuration
        """
        # Create standard directories
        directories = [
            "data",
            "pipelines",
            "dbt",
            "dbt/models",
            "dbt/models/staging",
            "dbt/models/marts",
            "logs",
        ]

        for dir_name in directories:
            (env_dir / dir_name).mkdir(parents=True, exist_ok=True)

        # Create .gitkeep files
        for dir_name in directories:
            gitkeep = env_dir / dir_name / ".gitkeep"
            gitkeep.touch(exist_ok=True)

    def _save_config(self, name: str, config: EnvironmentConfig) -> None:
        """
        Save environment configuration.

        Args:
            name: Environment name
            config: Configuration to save
        """
        env_dir = self.environments_dir / name
        config_path = env_dir / "config.json"
        save_environment_config(config, config_path)


def create_environment_manager(sbdk_home: Optional[Path] = None) -> EnvironmentManager:
    """
    Create an environment manager instance.

    Args:
        sbdk_home: Optional SBDK home directory

    Returns:
        EnvironmentManager instance

    Example:
        >>> manager = create_environment_manager()
        >>> env_path = manager.create("dev")
    """
    return EnvironmentManager(sbdk_home=sbdk_home)
