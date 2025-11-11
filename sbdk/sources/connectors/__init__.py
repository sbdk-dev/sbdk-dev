"""SBDK Data Source Connector Implementations."""

from sbdk.sources.connectors.csv_connector import (
    CSVConnector,
    CSVConnectorConfig,
    ColumnType,
    Encoding,
    FileFormat,
)

__all__ = [
    "CSVConnector",
    "CSVConnectorConfig",
    "ColumnType",
    "Encoding",
    "FileFormat",
]

# Optional imports - only load if dependencies available
try:
    from sbdk.sources.connectors.postgres_connector import (
        PostgresConfig,
        PostgresConnector,
        PostgresCursorMode,
        PostgresSSLMode,
    )
    __all__.extend([
        "PostgresConfig",
        "PostgresConnector",
        "PostgresCursorMode",
        "PostgresSSLMode",
    ])
except (ImportError, Exception):
    # PostgreSQL connector dependencies not installed
    # or raises DependencyError at module level
    pass
