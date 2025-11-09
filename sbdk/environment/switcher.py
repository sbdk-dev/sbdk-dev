"""
Environment Switcher

Fast environment switching with performance optimization (<2 seconds target).
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from sbdk.environment.config import EnvironmentConfig, load_environment_config
from sbdk.environment.manager import EnvironmentManager
from sbdk.exceptions import ValidationError


class EnvironmentSwitcher:
    """
    Fast environment switcher.

    Optimized for <2 second switching performance with caching and
    minimal validation.

    Example:
        >>> switcher = EnvironmentSwitcher()
        >>> elapsed = switcher.switch("dev")
        >>> print(f"Switched in {elapsed:.2f}s")
    """

    def __init__(self, manager: Optional[EnvironmentManager] = None):
        """
        Initialize environment switcher.

        Args:
            manager: EnvironmentManager instance (optional)
        """
        self.manager = manager or EnvironmentManager()
        self._cache: Dict[str, EnvironmentConfig] = {}

    def switch(self, name: str, validate: bool = True) -> float:
        """
        Switch to environment with performance tracking.

        Args:
            name: Environment name to switch to
            validate: Perform full validation (default: True)

        Returns:
            Elapsed time in seconds

        Raises:
            ValidationError: If environment doesn't exist or is invalid

        Example:
            >>> switcher = EnvironmentSwitcher()
            >>> elapsed = switcher.switch("dev")
            >>> assert elapsed < 2.0, "Switching took too long!"
        """
        start_time = time.time()

        # Fast path: minimal validation
        if not validate:
            self.manager.switch(name)
            return time.time() - start_time

        # Full validation path
        env_config = self._get_cached_config(name)

        # Verify environment is valid
        if not self._is_environment_valid(name, env_config):
            raise ValidationError(
                f"Environment '{name}' is invalid or corrupted",
                suggestion=f"Recreate environment: sbdk env delete {name} && sbdk env create {name}"
            )

        # Perform switch
        self.manager.switch(name)

        elapsed = time.time() - start_time

        # Performance warning
        if elapsed > 2.0:
            import warnings
            warnings.warn(
                f"Environment switch took {elapsed:.2f}s (target: <2s). "
                f"Consider optimizing environment structure.",
                RuntimeWarning
            )

        return elapsed

    def switch_with_validation(self, name: str) -> Dict[str, Any]:
        """
        Switch environment with comprehensive validation and reporting.

        Args:
            name: Environment name

        Returns:
            Switch result with timing and validation info

        Example:
            >>> switcher = EnvironmentSwitcher()
            >>> result = switcher.switch_with_validation("dev")
            >>> print(result["elapsed"])
        """
        start_time = time.time()
        validation_start = time.time()

        # Validate environment
        env_config = self._get_cached_config(name)
        is_valid = self._is_environment_valid(name, env_config)

        validation_time = time.time() - validation_start

        if not is_valid:
            raise ValidationError(
                f"Environment '{name}' failed validation",
                suggestion="Check environment configuration and structure"
            )

        # Perform switch
        switch_start = time.time()
        self.manager.switch(name)
        switch_time = time.time() - switch_start

        total_elapsed = time.time() - start_time

        return {
            "success": True,
            "environment": name,
            "elapsed": total_elapsed,
            "validation_time": validation_time,
            "switch_time": switch_time,
            "performance_target_met": total_elapsed < 2.0,
        }

    def get_switch_candidates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of environments available for switching.

        Returns:
            Dictionary mapping environment names to their info

        Example:
            >>> switcher = EnvironmentSwitcher()
            >>> candidates = switcher.get_switch_candidates()
            >>> for name, info in candidates.items():
            ...     print(f"{name}: {info['template']}")
        """
        environments = self.manager.list_environments()
        active = self.manager.get_active_environment()

        candidates = {}

        for env in environments:
            name = env["name"]

            # Skip active environment
            if name == active:
                continue

            candidates[name] = {
                "name": name,
                "template": env["template"],
                "target": env["target"],
                "description": env.get("description"),
                "can_switch": True,  # All environments are switchable
                "estimated_switch_time": "<2s",
            }

        return candidates

    def clear_cache(self) -> None:
        """
        Clear environment configuration cache.

        Use this if environments have been modified externally.
        """
        self._cache.clear()

    def _get_cached_config(self, name: str) -> EnvironmentConfig:
        """
        Get environment configuration with caching.

        Args:
            name: Environment name

        Returns:
            Environment configuration
        """
        if name not in self._cache:
            self._cache[name] = self.manager.get_environment(name)

        return self._cache[name]

    def _is_environment_valid(
        self,
        name: str,
        config: EnvironmentConfig
    ) -> bool:
        """
        Validate environment structure.

        Args:
            name: Environment name
            config: Environment configuration

        Returns:
            True if environment is valid
        """
        env_dir = self.manager.environments_dir / name

        # Check directory exists
        if not env_dir.exists():
            return False

        # Check config file exists
        config_path = env_dir / "config.json"
        if not config_path.exists():
            return False

        # Check required subdirectories exist
        required_dirs = ["data", "pipelines", "dbt"]
        for dir_name in required_dirs:
            if not (env_dir / dir_name).exists():
                return False

        return True


def create_environment_switcher(
    manager: Optional[EnvironmentManager] = None
) -> EnvironmentSwitcher:
    """
    Create an environment switcher instance.

    Args:
        manager: Optional EnvironmentManager instance

    Returns:
        EnvironmentSwitcher instance

    Example:
        >>> switcher = create_environment_switcher()
        >>> elapsed = switcher.switch("dev")
    """
    return EnvironmentSwitcher(manager=manager)
