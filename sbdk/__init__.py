"""
SBDK.dev - Local-first data pipeline sandbox toolkit

A comprehensive toolkit for building data pipelines using DLT, DuckDB, and dbt.
Perfect for local development, prototyping, and testing data workflows.
"""

__version__ = "1.1.0"
__author__ = "SBDK.dev Team"
__email__ = "hello@sbdk.dev"
__description__ = "🚀 SBDK.dev - Local-first data pipeline sandbox toolkit"

# Export main components for API usage
from sbdk.core.config import SBDKConfig
from sbdk.core.project import SBDKProject

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "SBDKConfig",
    "SBDKProject",
]
