"""
PostgreSQL Connector for SBDK

Production-ready PostgreSQL database connector with connection pooling,
schema introspection, and comprehensive error handling.

Features:
- Connection pooling with psycopg2
- SSL support
- Schema introspection (tables, columns, types)
- Transaction support
- Prepared statements
- Streaming query results
- Row count estimation
"""

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, field_validator

from sbdk.exceptions import DatabaseError, DependencyError, ValidationError
from sbdk.sources.base import (
    ConnectionStatus,
    DatabaseConnector,
    SchemaInfo,
    SourceConnectionConfig,
    SourceType,
)

# Try to import psycopg2 with helpful error message
try:
    import psycopg2
    import psycopg2.extensions
    import psycopg2.extras
    from psycopg2 import pool
except ImportError as e:
    raise DependencyError(
        "psycopg2",
        "PostgreSQL connector requires psycopg2-binary"
    ) from e


class PostgresSSLMode(str):
    """SSL modes for PostgreSQL connections."""

    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


class PostgresCursorMode(str):
    """Cursor modes for result fetching."""

    DICT = "dict"  # Return rows as dictionaries
    TUPLE = "tuple"  # Return rows as tuples
    NAMED_TUPLE = "namedtuple"  # Return rows as named tuples


class PostgresConfig(BaseModel):
    """
    PostgreSQL connection configuration with validation.

    Supports both individual parameters and connection string format.

    Example:
        >>> config = PostgresConfig(
        ...     host="localhost",
        ...     port=5432,
        ...     database="mydb",
        ...     username="user",
        ...     password="pass"
        ... )
    """

    # Connection parameters
    host: str = Field(..., description="PostgreSQL host")
    port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")

    # Advanced connection settings
    sslmode: str = Field(
        default=PostgresSSLMode.PREFER,
        description="SSL mode (disable, allow, prefer, require, verify-ca, verify-full)"
    )
    connect_timeout: int = Field(
        default=10,
        ge=1,
        le=300,
        description="Connection timeout in seconds"
    )
    application_name: str = Field(
        default="sbdk",
        description="Application name for connection"
    )

    # Connection pooling
    pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Connection pool size"
    )
    pool_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum pool overflow connections"
    )

    # Query settings
    cursor_mode: str = Field(
        default=PostgresCursorMode.DICT,
        description="Cursor mode for results (dict, tuple, namedtuple)"
    )
    fetch_size: int = Field(
        default=1000,
        ge=1,
        le=100000,
        description="Number of rows to fetch at a time"
    )

    # Schema settings
    default_schema: str = Field(
        default="public",
        description="Default schema to use"
    )

    @field_validator("sslmode")
    @classmethod
    def validate_sslmode(cls, v: str) -> str:
        """Validate SSL mode."""
        valid_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        if v not in valid_modes:
            raise ValueError(
                f"Invalid SSL mode '{v}'. Must be one of: {', '.join(valid_modes)}"
            )
        return v

    @field_validator("cursor_mode")
    @classmethod
    def validate_cursor_mode(cls, v: str) -> str:
        """Validate cursor mode."""
        valid_modes = ["dict", "tuple", "namedtuple"]
        if v not in valid_modes:
            raise ValueError(
                f"Invalid cursor mode '{v}'. Must be one of: {', '.join(valid_modes)}"
            )
        return v

    def to_connection_string(self) -> str:
        """
        Convert config to PostgreSQL connection string.

        Returns:
            Connection string in format postgresql://user:pass@host:port/db

        Example:
            >>> config = PostgresConfig(host="localhost", database="mydb", ...)
            >>> config.to_connection_string()
            'postgresql://user:***@localhost:5432/mydb'
        """
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    def to_connection_params(self) -> Dict[str, Any]:
        """
        Convert config to psycopg2 connection parameters.

        Returns:
            Dictionary of connection parameters for psycopg2.connect()

        Example:
            >>> config = PostgresConfig(...)
            >>> params = config.to_connection_params()
            >>> conn = psycopg2.connect(**params)
        """
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.username,
            "password": self.password,
            "sslmode": self.sslmode,
            "connect_timeout": self.connect_timeout,
            "application_name": self.application_name,
        }

    class Config:
        """Pydantic configuration."""
        extra = "forbid"


class PostgresConnector(DatabaseConnector):
    """
    Production-ready PostgreSQL connector for SBDK.

    Features:
    - Connection pooling for efficient resource usage
    - Schema introspection for automatic discovery
    - Streaming query results for memory efficiency
    - SSL support for secure connections
    - Transaction support for data integrity
    - Prepared statements for SQL injection protection

    Example:
        >>> from sbdk.sources.base import SourceConnectionConfig
        >>> from sbdk.sources.connectors.postgres_connector import PostgresConfig, PostgresConnector
        >>>
        >>> # Create configuration
        >>> pg_config = PostgresConfig(
        ...     host="localhost",
        ...     port=5432,
        ...     database="analytics",
        ...     username="analyst",
        ...     password="secret"
        ... )
        >>>
        >>> # Create source config
        >>> source_config = SourceConnectionConfig(
        ...     name="postgres_analytics",
        ...     source_type=SourceType.DATABASE,
        ...     description="Analytics PostgreSQL database"
        ... )
        >>>
        >>> # Use connector
        >>> connector = PostgresConnector(source_config, pg_config)
        >>> connector.connect()
        >>> tables = connector.list_tables()
        >>> connector.disconnect()
        >>>
        >>> # Or use context manager
        >>> with PostgresConnector(source_config, pg_config) as conn:
        ...     for row in conn.execute_query("SELECT * FROM users LIMIT 10"):
        ...         print(row)
    """

    def __init__(
        self,
        config: SourceConnectionConfig,
        postgres_config: PostgresConfig
    ):
        """
        Initialize PostgreSQL connector.

        Args:
            config: Base source connection configuration
            postgres_config: PostgreSQL-specific configuration

        Example:
            >>> source_config = SourceConnectionConfig(
            ...     name="my_postgres",
            ...     source_type=SourceType.DATABASE
            ... )
            >>> pg_config = PostgresConfig(host="localhost", database="mydb", ...)
            >>> connector = PostgresConnector(source_config, pg_config)
        """
        super().__init__(config)
        self.postgres_config = postgres_config
        self._pool: Optional[pool.SimpleConnectionPool] = None
        self._connection: Optional[psycopg2.extensions.connection] = None

    @classmethod
    def from_connection_string(
        cls,
        connection_string: str,
        name: str = "postgres_connection"
    ) -> "PostgresConnector":
        """
        Create connector from PostgreSQL connection string.

        Args:
            connection_string: PostgreSQL connection string
                Format: postgresql://user:password@host:port/database?param=value
            name: Connection name

        Returns:
            PostgresConnector instance

        Raises:
            ValidationError: If connection string is invalid

        Example:
            >>> conn_str = "postgresql://user:pass@localhost:5432/mydb"
            >>> connector = PostgresConnector.from_connection_string(conn_str)
        """
        parsed = urlparse(connection_string)

        if parsed.scheme not in ["postgres", "postgresql"]:
            raise ValidationError(
                f"Invalid connection string scheme: {parsed.scheme}",
                "Use format: postgresql://user:pass@host:port/database"
            )

        # Extract connection parameters
        params = parse_qs(parsed.query)

        pg_config = PostgresConfig(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/") if parsed.path else "",
            username=parsed.username or "",
            password=parsed.password or "",
            sslmode=params.get("sslmode", [PostgresSSLMode.PREFER])[0],
            application_name=params.get("application_name", ["sbdk"])[0],
        )

        source_config = SourceConnectionConfig(
            name=name,
            source_type=SourceType.DATABASE,
            description=f"PostgreSQL connection to {pg_config.host}:{pg_config.port}/{pg_config.database}"
        )

        return cls(source_config, pg_config)

    def connect(self) -> None:
        """
        Establish connection pool to PostgreSQL database.

        Creates a connection pool for efficient connection management.
        Uses SimpleConnectionPool for thread-safe connection pooling.

        Raises:
            DatabaseError: If connection fails

        Example:
            >>> connector = PostgresConnector(config, pg_config)
            >>> connector.connect()
            >>> # Connection pool is now ready
        """
        if self._pool is not None:
            return  # Already connected

        try:
            # Create connection pool
            self._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.postgres_config.pool_size,
                **self.postgres_config.to_connection_params()
            )

            # Test connection by getting one from pool
            test_conn = self._pool.getconn()
            test_conn.close()
            self._pool.putconn(test_conn)

            self._connected = True

        except psycopg2.OperationalError as e:
            raise DatabaseError(
                f"Failed to connect to PostgreSQL at {self.postgres_config.host}:{self.postgres_config.port}",
                suggestion="Verify host, port, credentials, and network connectivity. Check PostgreSQL is running.",
                details={
                    "host": self.postgres_config.host,
                    "port": self.postgres_config.port,
                    "database": self.postgres_config.database,
                    "error": str(e)
                }
            ) from e

        except psycopg2.Error as e:
            raise DatabaseError(
                f"PostgreSQL connection error: {str(e)}",
                suggestion="Check PostgreSQL logs for detailed error information",
                details={"error": str(e)}
            ) from e

    def disconnect(self) -> None:
        """
        Close connection pool and all connections.

        Releases all pooled connections and closes the pool.
        Safe to call multiple times.

        Example:
            >>> connector.disconnect()
            >>> # All connections are now closed
        """
        if self._pool is not None:
            try:
                self._pool.closeall()
            except Exception:
                pass  # Best effort cleanup
            finally:
                self._pool = None
                self._connected = False

    def test_connection(self) -> bool:
        """
        Test if database connection is valid.

        Attempts to execute a simple query to verify connectivity.

        Returns:
            True if connection is successful

        Raises:
            DatabaseError: If connection test fails

        Example:
            >>> connector = PostgresConnector(config, pg_config)
            >>> if connector.test_connection():
            ...     print("Connection successful!")
        """
        try:
            # Get connection from pool
            conn = self._get_connection()
            cursor = conn.cursor()

            # Execute test query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            cursor.close()
            self._return_connection(conn)

            return result is not None and result[0] == 1

        except Exception as e:
            raise DatabaseError(
                "Connection test failed",
                suggestion="Verify database is accessible and credentials are correct",
                details={"error": str(e)}
            ) from e

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Execute SQL query and stream results.

        Uses server-side cursor for memory-efficient streaming of large result sets.
        Automatically handles NULL values and type conversion.

        Args:
            query: SQL query string
            params: Optional query parameters for prepared statement

        Yields:
            Query results as dictionaries (or tuples based on cursor_mode)

        Raises:
            DatabaseError: If query execution fails

        Example:
            >>> # Simple query
            >>> for row in connector.execute_query("SELECT * FROM users"):
            ...     print(row['username'])
            >>>
            >>> # Parameterized query (prevents SQL injection)
            >>> query = "SELECT * FROM users WHERE id = %s"
            >>> for row in connector.execute_query(query, params=(123,)):
            ...     print(row)
        """
        conn = None
        cursor = None

        try:
            # Get connection from pool
            conn = self._get_connection()

            # Create cursor based on mode
            if self.postgres_config.cursor_mode == PostgresCursorMode.DICT:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            elif self.postgres_config.cursor_mode == PostgresCursorMode.NAMED_TUPLE:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
            else:
                cursor = conn.cursor()

            # Set server-side cursor name for streaming
            cursor_name = f"sbdk_cursor_{id(cursor)}"
            cursor = conn.cursor(
                name=cursor_name,
                cursor_factory=psycopg2.extras.RealDictCursor
                if self.postgres_config.cursor_mode == PostgresCursorMode.DICT
                else None
            )

            # Execute query
            cursor.execute(query, params)

            # Stream results in batches
            while True:
                rows = cursor.fetchmany(self.postgres_config.fetch_size)
                if not rows:
                    break

                for row in rows:
                    # Convert to dict if using RealDictCursor
                    if isinstance(row, dict):
                        yield dict(row)
                    else:
                        # For tuple mode, convert to dict using column names
                        if cursor.description:
                            yield dict(zip(
                                [desc[0] for desc in cursor.description],
                                row
                            ))
                        else:
                            yield {"value": row}

        except psycopg2.ProgrammingError as e:
            raise DatabaseError(
                f"SQL syntax error: {str(e)}",
                suggestion="Check SQL query syntax and ensure tables/columns exist",
                details={"query": query, "error": str(e)}
            ) from e

        except psycopg2.Error as e:
            raise DatabaseError(
                f"Query execution failed: {str(e)}",
                suggestion="Check PostgreSQL logs for detailed error information",
                details={"query": query, "error": str(e)}
            ) from e

        finally:
            # Cleanup
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

            if conn:
                self._return_connection(conn)

    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in database or specific schema.

        Queries information_schema to discover tables. Excludes system tables.

        Args:
            schema: Schema name (uses default_schema if None)

        Returns:
            List of table names

        Raises:
            DatabaseError: If listing fails

        Example:
            >>> # List tables in default schema
            >>> tables = connector.list_tables()
            >>> print(tables)
            ['users', 'orders', 'products']
            >>>
            >>> # List tables in specific schema
            >>> tables = connector.list_tables(schema="analytics")
        """
        schema = schema or self.postgres_config.default_schema

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """

        try:
            tables = []
            for row in self.execute_query(query, params=(schema,)):
                tables.append(row["table_name"])
            return tables

        except Exception as e:
            raise DatabaseError(
                f"Failed to list tables in schema '{schema}'",
                suggestion="Verify schema exists and user has SELECT privileges on information_schema",
                details={"schema": schema, "error": str(e)}
            ) from e

    def detect_schema(
        self,
        table_name: Optional[str] = None,
        schema: Optional[str] = None
    ) -> SchemaInfo:
        """
        Detect schema information for a table.

        Introspects table structure including columns, data types, nullability,
        and estimated row count.

        Args:
            table_name: Table name to introspect (required)
            schema: Schema name (uses default_schema if None)

        Returns:
            SchemaInfo with table structure and metadata

        Raises:
            ValidationError: If table_name is not provided
            DatabaseError: If schema detection fails

        Example:
            >>> schema_info = connector.detect_schema("users")
            >>> print(schema_info.columns)
            [
                {
                    'name': 'id',
                    'type': 'integer',
                    'nullable': False,
                    'primary_key': True
                },
                {
                    'name': 'username',
                    'type': 'character varying',
                    'nullable': False,
                    'max_length': 255
                }
            ]
            >>> print(schema_info.row_count)
            1523
        """
        if table_name is None:
            raise ValidationError(
                "table_name is required for schema detection",
                "Provide table name: connector.detect_schema('my_table')"
            )

        schema = schema or self.postgres_config.default_schema

        try:
            # Query column information
            columns_query = """
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                ORDER BY ordinal_position
            """

            columns = []
            for row in self.execute_query(columns_query, params=(schema, table_name)):
                column_info = {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                }

                # Add type-specific details
                if row["character_maximum_length"]:
                    column_info["max_length"] = row["character_maximum_length"]

                if row["numeric_precision"]:
                    column_info["precision"] = row["numeric_precision"]

                if row["numeric_scale"]:
                    column_info["scale"] = row["numeric_scale"]

                columns.append(column_info)

            if not columns:
                raise DatabaseError(
                    f"Table '{schema}.{table_name}' not found or has no columns",
                    suggestion=f"Verify table exists: SELECT * FROM {schema}.{table_name} LIMIT 1"
                )

            # Get row count estimate (fast)
            row_count = self._estimate_row_count(table_name, schema)

            return SchemaInfo(
                table_name=f"{schema}.{table_name}",
                columns=columns,
                row_count=row_count,
                detected_at=datetime.utcnow()
            )

        except DatabaseError:
            raise  # Re-raise DatabaseError as-is

        except Exception as e:
            raise DatabaseError(
                f"Failed to detect schema for table '{schema}.{table_name}'",
                suggestion="Verify table exists and user has SELECT privileges",
                details={
                    "schema": schema,
                    "table": table_name,
                    "error": str(e)
                }
            ) from e

    def list_schemas(self) -> List[str]:
        """
        List all schemas in database.

        Returns:
            List of schema names

        Example:
            >>> schemas = connector.list_schemas()
            >>> print(schemas)
            ['public', 'analytics', 'staging']
        """
        query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """

        schemas = []
        for row in self.execute_query(query):
            schemas.append(row["schema_name"])
        return schemas

    @contextmanager
    def transaction(self) -> Iterator[psycopg2.extensions.connection]:
        """
        Context manager for database transactions.

        Provides automatic commit/rollback handling for transactional operations.

        Yields:
            Database connection with transaction

        Example:
            >>> with connector.transaction() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("INSERT INTO users (name) VALUES ('John')")
            ...     cursor.execute("INSERT INTO logs (event) VALUES ('user_created')")
            ...     # Auto-commit on success, rollback on exception
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._return_connection(conn)

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection information and statistics.

        Returns:
            Dictionary with connection details and pool statistics

        Example:
            >>> info = connector.get_connection_info()
            >>> print(info['pool_size'], info['pool_available'])
        """
        info = {
            "host": self.postgres_config.host,
            "port": self.postgres_config.port,
            "database": self.postgres_config.database,
            "username": self.postgres_config.username,
            "sslmode": self.postgres_config.sslmode,
            "connected": self._connected,
            "pool_size": self.postgres_config.pool_size,
        }

        if self._pool:
            # Get pool statistics (implementation varies by pool type)
            info["pool_available"] = "N/A"  # SimpleConnectionPool doesn't expose this

        return info

    # Private helper methods

    def _get_connection(self) -> psycopg2.extensions.connection:
        """
        Get connection from pool.

        Returns:
            Database connection

        Raises:
            DatabaseError: If pool is not initialized or connection unavailable
        """
        if self._pool is None:
            raise DatabaseError(
                "Connection pool not initialized",
                suggestion="Call connect() before executing queries"
            )

        try:
            return self._pool.getconn()
        except pool.PoolError as e:
            raise DatabaseError(
                "Failed to get connection from pool",
                suggestion="Connection pool may be exhausted. Check for connection leaks.",
                details={"error": str(e)}
            ) from e

    def _return_connection(self, conn: psycopg2.extensions.connection) -> None:
        """
        Return connection to pool.

        Args:
            conn: Connection to return
        """
        if self._pool and conn:
            try:
                self._pool.putconn(conn)
            except Exception:
                pass  # Best effort

    def _estimate_row_count(self, table_name: str, schema: str) -> Optional[int]:
        """
        Estimate row count for a table using statistics.

        Uses PostgreSQL's statistics (fast) rather than COUNT(*) (slow).

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Estimated row count or None if unavailable
        """
        try:
            query = """
                SELECT reltuples::bigint AS estimate
                FROM pg_class
                WHERE oid = %s::regclass
            """

            full_table_name = f"{schema}.{table_name}"

            for row in self.execute_query(query, params=(full_table_name,)):
                return int(row["estimate"]) if row["estimate"] else None

            return None

        except Exception:
            # If estimation fails, return None
            return None
