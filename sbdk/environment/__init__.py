"""
SBDK Environment Management

Provides environment management capabilities for SBDK:
- Create and manage multiple environments (dev/staging/prod)
- Switch between environments quickly (<2 seconds)
- Template-based environment creation
- Isolated configurations per environment

Example:
    >>> from sbdk.environment import EnvironmentManager, EnvironmentTemplate
    >>> manager = EnvironmentManager()
    >>> env_path = manager.create("dev", template=EnvironmentTemplate.ANALYTICS)
    >>> manager.switch("dev")
    >>> environments = manager.list_environments()
"""

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
from sbdk.environment.manager import EnvironmentManager, create_environment_manager
from sbdk.environment.switcher import EnvironmentSwitcher, create_environment_switcher
from sbdk.environment.template import TemplateEngine, create_template_engine

__all__ = [
    # Config
    "EnvironmentConfig",
    "EnvironmentFeatures",
    "EnvironmentPerformance",
    "EnvironmentStatus",
    "EnvironmentTarget",
    "EnvironmentTemplate",
    "ActiveEnvironmentMarker",
    "create_environment_config",
    "load_environment_config",
    "save_environment_config",
    # Manager
    "EnvironmentManager",
    "create_environment_manager",
    # Switcher
    "EnvironmentSwitcher",
    "create_environment_switcher",
    # Template
    "TemplateEngine",
    "create_template_engine",
]
