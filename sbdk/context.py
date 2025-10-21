"""
SBDK Context Manager

Centralized context management for CLI operations, providing consistent access to:
- Configuration
- Logging
- State management
- Resource cleanup

Inspired by Click's Context pattern and spec-kit's modular architecture.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.logging import RichHandler

from sbdk.exceptions import ConfigurationError, ProjectNotFoundError


class SBDKContext:
    """
    Central context object for SBDK CLI operations.

    Manages configuration, logging, state, and resources throughout
    the CLI command lifecycle. Uses singleton pattern to ensure
    consistent state across command execution.

    Attributes:
        project_dir: Path to SBDK project root
        config: Loaded configuration dictionary
        console: Rich Console for formatted output
        logger: Configured logging instance
        verbose: Verbose output mode
        quiet: Quiet mode (minimal output)
        dry_run: Dry-run mode (no destructive operations)
    """

    _instance: Optional["SBDKContext"] = None

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        config_file: str = "sbdk_config.json",
        verbose: bool = False,
        quiet: bool = False,
        dry_run: bool = False
    ):
        """
        Initialize SBDK context.

        Args:
            project_dir: Project directory path (default: current directory)
            config_file: Configuration file name
            verbose: Enable verbose output
            quiet: Enable quiet mode
            dry_run: Enable dry-run mode
        """
        self.project_dir = Path(project_dir or Path.cwd())
        self.config_file = config_file
        self.verbose = verbose
        self.quiet = quiet
        self.dry_run = dry_run

        # Initialize components
        self.console = self._setup_console()
        self.logger = self._setup_logging()
        self._config: Optional[dict[str, Any]] = None
        self._state: dict[str, Any] = {}

        # Track resources for cleanup
        self._resources: list[Any] = []

    @classmethod
    def get_instance(cls) -> "SBDKContext":
        """
        Get or create singleton context instance.

        Returns:
            Global SBDK context instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def create(
        cls,
        project_dir: Optional[Path] = None,
        config_file: str = "sbdk_config.json",
        verbose: bool = False,
        quiet: bool = False,
        dry_run: bool = False
    ) -> "SBDKContext":
        """
        Create new context instance (replaces existing singleton).

        Args:
            project_dir: Project directory path
            config_file: Configuration file name
            verbose: Enable verbose output
            quiet: Enable quiet mode
            dry_run: Enable dry-run mode

        Returns:
            New SBDK context instance
        """
        cls._instance = cls(project_dir, config_file, verbose, quiet, dry_run)
        return cls._instance

    def _setup_console(self) -> Console:
        """
        Set up Rich console for formatted output.

        Returns:
            Configured Rich Console instance
        """
        return Console(
            stderr=False,
            quiet=self.quiet,
            force_terminal=not self.quiet,
            color_system="auto"
        )

    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging with appropriate level and handlers.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("sbdk")

        # Set level based on mode
        if self.verbose:
            logger.setLevel(logging.DEBUG)
        elif self.quiet:
            logger.setLevel(logging.ERROR)
        else:
            logger.setLevel(logging.INFO)

        # Remove existing handlers
        logger.handlers = []

        # Add Rich handler for pretty logging
        handler = RichHandler(
            console=self.console,
            show_time=self.verbose,
            show_path=self.verbose,
            markup=True,
            rich_tracebacks=True
        )

        # Set format
        if self.verbose:
            formatter = logging.Formatter(
                "%(name)s - %(levelname)s - %(message)s"
            )
        else:
            formatter = logging.Formatter("%(message)s")

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # File handler for persistent logs
        log_file = self.project_dir / ".sbdk" / "logs" / "sbdk.log"
        if self.project_dir.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    @property
    def config(self) -> dict[str, Any]:
        """
        Get project configuration (lazy loaded).

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If config file is invalid
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self, force_reload: bool = False) -> dict[str, Any]:
        """
        Load configuration from file.

        Args:
            force_reload: Force reload even if already loaded

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If config file is invalid or missing
        """
        if self._config is not None and not force_reload:
            return self._config

        config_path = self.project_dir / self.config_file

        if not config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}",
                suggestion="Run 'sbdk init' to create a new project or check your current directory"
            )

        try:
            import json
            with open(config_path) as f:
                self._config = json.load(f)

            self.logger.debug(f"Loaded configuration from {config_path}")
            return self._config

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {e}",
                suggestion="Check your sbdk_config.json for syntax errors"
            ) from e

    def save_config(self, config: Optional[dict[str, Any]] = None) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save (uses current if None)

        Raises:
            ConfigurationError: If save operation fails
        """
        if config is not None:
            self._config = config

        config_path = self.project_dir / self.config_file

        try:
            import json
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=2)

            self.logger.debug(f"Saved configuration to {config_path}")

        except (IOError, OSError) as e:
            raise ConfigurationError(
                f"Failed to save configuration: {e}",
                suggestion="Check file permissions and disk space"
            ) from e

    def verify_project_structure(self) -> bool:
        """
        Verify SBDK project structure exists.

        Returns:
            True if valid project structure

        Raises:
            ProjectNotFoundError: If not a valid SBDK project
        """
        config_path = self.project_dir / self.config_file

        if not config_path.exists():
            raise ProjectNotFoundError(str(self.project_dir))

        # Check for essential directories
        essential_dirs = ["pipelines", "dbt", "data"]
        missing_dirs = [
            d for d in essential_dirs
            if not (self.project_dir / d).exists()
        ]

        if missing_dirs:
            self.logger.warning(
                f"Project structure incomplete. Missing directories: {', '.join(missing_dirs)}"
            )

        return True

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get value from context state.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """
        Set value in context state.

        Args:
            key: State key
            value: Value to set
        """
        self._state[key] = value
        self.logger.debug(f"Set state: {key} = {value}")

    def register_resource(self, resource: Any) -> None:
        """
        Register resource for cleanup on context exit.

        Args:
            resource: Resource object (must have close() method)
        """
        self._resources.append(resource)

    def cleanup(self) -> None:
        """
        Clean up registered resources.

        Called automatically on context exit or can be called manually.
        """
        self.logger.debug("Cleaning up context resources")

        for resource in reversed(self._resources):
            try:
                if hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, '__exit__'):
                    resource.__exit__(None, None, None)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup resource: {e}")

        self._resources.clear()

    def __enter__(self) -> "SBDKContext":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()


# Global context accessor functions

def get_context() -> SBDKContext:
    """
    Get global SBDK context instance.

    Returns:
        Global context instance
    """
    return SBDKContext.get_instance()


def create_context(
    project_dir: Optional[Path] = None,
    config_file: str = "sbdk_config.json",
    verbose: bool = False,
    quiet: bool = False,
    dry_run: bool = False
) -> SBDKContext:
    """
    Create new SBDK context (replaces existing).

    Args:
        project_dir: Project directory path
        config_file: Configuration file name
        verbose: Enable verbose output
        quiet: Enable quiet mode
        dry_run: Enable dry-run mode

    Returns:
        New context instance
    """
    return SBDKContext.create(project_dir, config_file, verbose, quiet, dry_run)
