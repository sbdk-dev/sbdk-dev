"""
SBDK Data Source Connectors

Provides connectors for various data sources:
- Databases (PostgreSQL, MySQL, etc.)
- Files (CSV, JSON, Parquet)
- APIs (REST, GraphQL)

Example:
    >>> from sbdk.sources import CSVConnector, SamplingConfig, SamplingStrategy
    >>> config = SourceConnectionConfig(name="users", source_type=SourceType.FILE)
    >>> connector = CSVConnector(config, file_path="users.csv")
    >>> sample = connector.get_sample(SamplingConfig(strategy=SamplingStrategy.LIMIT, limit=100))
"""

from sbdk.sources.base import (
    BaseConnector,
    ConnectionStatus,
    DatabaseConnector,
    FileConnector,
    SamplingConfig,
    SamplingStrategy,
    SchemaInfo,
    SourceConnectionConfig,
    SourceType,
)

__all__ = [
    "BaseConnector",
    "DatabaseConnector",
    "FileConnector",
    "ConnectionStatus",
    "SamplingConfig",
    "SamplingStrategy",
    "SchemaInfo",
    "SourceConnectionConfig",
    "SourceType",
]
