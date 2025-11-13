"""
Base Connector Framework for SBDK Data Sources

Provides abstract base classes and common functionality for all data source
connectors (PostgreSQL, CSV, APIs, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from pydantic import BaseModel, Field


class SamplingStrategy(str, Enum):
    """Data sampling strategies."""

    FULL = "full"  # Load all data
    PERCENTAGE = "percentage"  # Sample by percentage (e.g., 10%)
    LIMIT = "limit"  # Sample first N rows
    RANDOM = "random"  # Random sampling
    INTELLIGENT = "intelligent"  # Smart sampling based on data distribution


class SourceType(str, Enum):
    """Data source types."""

    DATABASE = "database"
    FILE = "file"
    API = "api"
    STREAM = "stream"


class ConnectionStatus(str, Enum):
    """Connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TESTING = "testing"


@dataclass
class SamplingConfig:
    """Configuration for data sampling."""

    strategy: SamplingStrategy = SamplingStrategy.FULL
    percentage: Optional[float] = None  # For PERCENTAGE strategy (0-100)
    limit: Optional[int] = None  # For LIMIT strategy
    seed: Optional[int] = None  # For RANDOM strategy


class SourceConnectionConfig(BaseModel):
    """Base configuration for data source connections."""

    name: str = Field(..., description="Connection name")
    source_type: SourceType = Field(..., description="Type of data source")
    description: Optional[str] = Field(None, description="Connection description")
    sampling: SamplingConfig = Field(
        default_factory=SamplingConfig,
        description="Sampling configuration"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class SchemaInfo(BaseModel):
    """Schema information for a data source."""

    table_name: str
    columns: List[Dict[str, Any]]
    row_count: Optional[int] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {datetime: lambda v: v.isoformat()}


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.

    All connectors must implement:
    - connect(): Establish connection
    - disconnect(): Close connection
    - test_connection(): Verify connectivity
    - fetch_data(): Retrieve data
    - detect_schema(): Discover schema
    - get_sample(): Get data sample

    Example:
        >>> class MyConnector(BaseConnector):
        ...     def connect(self):
        ...         # Implementation
        ...         pass
    """

    def __init__(self, config: SourceConnectionConfig):
        """
        Initialize connector.

        Args:
            config: Connection configuration
        """
        self.config = config
        self._connected = False
        self._connection = None

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to data source.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to data source.
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if connection is valid.

        Returns:
            True if connection is successful

        Raises:
            ConnectionError: If connection test fails
        """
        pass

    @abstractmethod
    def fetch_data(
        self,
        query: Optional[str] = None,
        **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        Fetch data from source.

        Args:
            query: Optional query/filter
            **kwargs: Additional source-specific parameters

        Yields:
            Data records as dictionaries

        Raises:
            DataFetchError: If data fetch fails
        """
        pass

    @abstractmethod
    def detect_schema(self, table_name: Optional[str] = None) -> SchemaInfo:
        """
        Detect schema of data source.

        Args:
            table_name: Optional specific table/resource

        Returns:
            Schema information

        Raises:
            SchemaDetectionError: If schema detection fails
        """
        pass

    def get_sample(
        self,
        sample_config: Optional[SamplingConfig] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Get data sample based on sampling strategy.

        Args:
            sample_config: Sampling configuration (uses default if None)

        Yields:
            Sampled data records

        Example:
            >>> connector = MyConnector(config)
            >>> sample = connector.get_sample(SamplingConfig(strategy=SamplingStrategy.LIMIT, limit=100))
        """
        config = sample_config or self.config.sampling

        if config.strategy == SamplingStrategy.FULL:
            yield from self.fetch_data()
        elif config.strategy == SamplingStrategy.LIMIT:
            yield from self._sample_limit(config.limit or 1000)
        elif config.strategy == SamplingStrategy.PERCENTAGE:
            yield from self._sample_percentage(config.percentage or 10.0)
        elif config.strategy == SamplingStrategy.RANDOM:
            yield from self._sample_random(config.percentage or 10.0, config.seed)
        elif config.strategy == SamplingStrategy.INTELLIGENT:
            yield from self._sample_intelligent()

    def _sample_limit(self, limit: int) -> Iterator[Dict[str, Any]]:
        """Sample first N rows."""
        count = 0
        for record in self.fetch_data():
            if count >= limit:
                break
            yield record
            count += 1

    def _sample_percentage(self, percentage: float) -> Iterator[Dict[str, Any]]:
        """Sample by percentage."""
        import random
        for record in self.fetch_data():
            if random.random() * 100 < percentage:
                yield record

    def _sample_random(self, percentage: float, seed: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Random sampling with optional seed."""
        import random
        if seed:
            random.seed(seed)

        # Load all data (for true random sampling)
        data = list(self.fetch_data())
        sample_size = int(len(data) * percentage / 100)
        sample = random.sample(data, min(sample_size, len(data)))

        yield from sample

    def _sample_intelligent(self) -> Iterator[Dict[str, Any]]:
        """
        Intelligent sampling based on data distribution.

        Default implementation uses stratified sampling if possible,
        falls back to limit-based sampling.
        """
        # Default: sample first 1000 rows
        # Subclasses can override for smarter sampling
        yield from self._sample_limit(1000)

    def get_status(self) -> Dict[str, Any]:
        """
        Get connection status.

        Returns:
            Status dictionary with connection info
        """
        return {
            "name": self.config.name,
            "source_type": self.config.source_type.value,
            "connected": self._connected,
            "description": self.config.description,
            "sampling": {
                "strategy": self.config.sampling.strategy.value,
                "percentage": self.config.sampling.percentage,
                "limit": self.config.sampling.limit,
            }
        }

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class DatabaseConnector(BaseConnector):
    """
    Base class for database connectors.

    Provides common database-specific functionality.
    """

    @abstractmethod
    def execute_query(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Execute SQL query.

        Args:
            query: SQL query string

        Yields:
            Query results as dictionaries
        """
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        """
        List all tables in database.

        Returns:
            List of table names
        """
        pass

    def fetch_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        Fetch data from database.

        Args:
            query: SQL query (takes precedence over table)
            table: Table name to fetch from
            **kwargs: Additional parameters

        Yields:
            Data records
        """
        if query:
            yield from self.execute_query(query)
        elif table:
            yield from self.execute_query(f"SELECT * FROM {table}")
        else:
            raise ValueError("Either 'query' or 'table' must be specified")


class FileConnector(BaseConnector):
    """
    Base class for file-based connectors.

    Provides common file handling functionality.
    """

    def __init__(self, config: SourceConnectionConfig, file_path: Path):
        """
        Initialize file connector.

        Args:
            config: Connection configuration
            file_path: Path to file
        """
        super().__init__(config)
        self.file_path = Path(file_path)

    @abstractmethod
    def parse_file(self) -> Iterator[Dict[str, Any]]:
        """
        Parse file and yield records.

        Yields:
            Parsed records as dictionaries
        """
        pass

    def connect(self) -> None:
        """Validate file exists."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        self._connected = True

    def disconnect(self) -> None:
        """Close file handles."""
        self._connected = False

    def test_connection(self) -> bool:
        """Test if file is accessible."""
        return self.file_path.exists() and self.file_path.is_file()

    def fetch_data(
        self,
        query: Optional[str] = None,
        **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        Fetch data from file.

        Args:
            query: Optional filter (not used for files)
            **kwargs: Additional parameters

        Yields:
            File records
        """
        yield from self.parse_file()
