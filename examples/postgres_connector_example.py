"""
PostgreSQL Connector Usage Examples

Demonstrates how to use the PostgreSQL connector in SBDK for various scenarios.
"""

from sbdk.sources.base import SourceConnectionConfig, SourceType
from sbdk.sources.connectors import PostgresConfig, PostgresConnector


def example_basic_connection():
    """Basic connection and query example."""
    print("\n=== Example 1: Basic Connection ===")

    # Create PostgreSQL configuration
    pg_config = PostgresConfig(
        host="localhost",
        port=5432,
        database="analytics",
        username="analyst",
        password="secret",
        sslmode="prefer"
    )

    # Create source configuration
    source_config = SourceConnectionConfig(
        name="analytics_db",
        source_type=SourceType.DATABASE,
        description="Analytics PostgreSQL database"
    )

    # Connect and query
    connector = PostgresConnector(source_config, pg_config)
    connector.connect()

    try:
        # List all tables
        tables = connector.list_tables()
        print(f"Found {len(tables)} tables: {tables}")

        # Execute a simple query
        query = "SELECT * FROM users LIMIT 5"
        print(f"\nExecuting: {query}")

        for row in connector.execute_query(query):
            print(row)

    finally:
        connector.disconnect()


def example_context_manager():
    """Using context manager for automatic cleanup."""
    print("\n=== Example 2: Context Manager ===")

    pg_config = PostgresConfig(
        host="localhost",
        database="mydb",
        username="user",
        password="pass"
    )

    source_config = SourceConnectionConfig(
        name="mydb",
        source_type=SourceType.DATABASE
    )

    # Context manager automatically handles connect/disconnect
    with PostgresConnector(source_config, pg_config) as conn:
        tables = conn.list_tables()
        print(f"Tables: {tables}")


def example_connection_string():
    """Creating connector from connection string."""
    print("\n=== Example 3: Connection String ===")

    # Create from connection string
    conn_str = "postgresql://user:password@localhost:5432/analytics?sslmode=require"
    connector = PostgresConnector.from_connection_string(
        conn_str,
        name="analytics_connection"
    )

    with connector:
        print(f"Connected to: {connector.get_connection_info()}")
        schemas = connector.list_schemas()
        print(f"Available schemas: {schemas}")


def example_schema_introspection():
    """Introspecting table schemas."""
    print("\n=== Example 4: Schema Introspection ===")

    pg_config = PostgresConfig(
        host="localhost",
        database="analytics",
        username="analyst",
        password="secret"
    )

    source_config = SourceConnectionConfig(
        name="analytics",
        source_type=SourceType.DATABASE
    )

    with PostgresConnector(source_config, pg_config) as conn:
        # Detect schema for a table
        schema_info = conn.detect_schema("users")

        print(f"\nTable: {schema_info.table_name}")
        print(f"Row count (estimate): {schema_info.row_count:,}")
        print(f"Detected at: {schema_info.detected_at}")
        print("\nColumns:")

        for col in schema_info.columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            type_info = col["type"]

            if "max_length" in col:
                type_info += f"({col['max_length']})"

            print(f"  - {col['name']}: {type_info} {nullable}")


def example_parameterized_queries():
    """Using parameterized queries to prevent SQL injection."""
    print("\n=== Example 5: Parameterized Queries ===")

    pg_config = PostgresConfig(
        host="localhost",
        database="mydb",
        username="user",
        password="pass"
    )

    source_config = SourceConnectionConfig(
        name="mydb",
        source_type=SourceType.DATABASE
    )

    with PostgresConnector(source_config, pg_config) as conn:
        # Safe parameterized query
        query = """
            SELECT *
            FROM users
            WHERE created_at > %s
              AND status = %s
            LIMIT %s
        """

        params = ("2024-01-01", "active", 10)

        print(f"Executing parameterized query...")
        for row in conn.execute_query(query, params=params):
            print(row)


def example_transactions():
    """Using transactions for atomic operations."""
    print("\n=== Example 6: Transactions ===")

    pg_config = PostgresConfig(
        host="localhost",
        database="mydb",
        username="user",
        password="pass"
    )

    source_config = SourceConnectionConfig(
        name="mydb",
        source_type=SourceType.DATABASE
    )

    connector = PostgresConnector(source_config, pg_config)
    connector.connect()

    try:
        # Use transaction context manager
        with connector.transaction() as conn:
            cursor = conn.cursor()

            # Multiple operations in transaction
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (%s, %s)",
                ("john_doe", "john@example.com")
            )

            cursor.execute(
                "INSERT INTO audit_log (event, user) VALUES (%s, %s)",
                ("user_created", "john_doe")
            )

            # Transaction commits automatically on success
            # or rolls back on exception

    finally:
        connector.disconnect()


def example_streaming_large_results():
    """Streaming large result sets efficiently."""
    print("\n=== Example 7: Streaming Large Results ===")

    pg_config = PostgresConfig(
        host="localhost",
        database="analytics",
        username="analyst",
        password="secret",
        fetch_size=5000  # Fetch 5000 rows at a time
    )

    source_config = SourceConnectionConfig(
        name="analytics",
        source_type=SourceType.DATABASE
    )

    with PostgresConnector(source_config, pg_config) as conn:
        # Query large table
        query = "SELECT * FROM large_events_table"

        print("Streaming large result set...")
        count = 0

        for row in conn.execute_query(query):
            count += 1
            if count % 10000 == 0:
                print(f"  Processed {count:,} rows...")

        print(f"Total: {count:,} rows processed")


def example_multiple_schemas():
    """Working with multiple schemas."""
    print("\n=== Example 8: Multiple Schemas ===")

    pg_config = PostgresConfig(
        host="localhost",
        database="analytics",
        username="analyst",
        password="secret",
        default_schema="public"
    )

    source_config = SourceConnectionConfig(
        name="analytics",
        source_type=SourceType.DATABASE
    )

    with PostgresConnector(source_config, pg_config) as conn:
        # List all schemas
        schemas = conn.list_schemas()
        print(f"Available schemas: {schemas}")

        # List tables in each schema
        for schema in schemas:
            tables = conn.list_tables(schema=schema)
            print(f"\n{schema}.* tables:")
            for table in tables:
                print(f"  - {schema}.{table}")


def example_connection_pooling():
    """Connection pooling for concurrent access."""
    print("\n=== Example 9: Connection Pooling ===")

    pg_config = PostgresConfig(
        host="localhost",
        database="mydb",
        username="user",
        password="pass",
        pool_size=10,  # Pool of 10 connections
        pool_max_overflow=5  # Allow 5 additional connections
    )

    source_config = SourceConnectionConfig(
        name="mydb",
        source_type=SourceType.DATABASE
    )

    connector = PostgresConnector(source_config, pg_config)
    connector.connect()

    try:
        # Get connection info
        info = connector.get_connection_info()
        print(f"Connection pool info:")
        print(f"  Host: {info['host']}:{info['port']}")
        print(f"  Database: {info['database']}")
        print(f"  Pool size: {info['pool_size']}")
        print(f"  Connected: {info['connected']}")

        # Multiple queries can reuse connections from pool
        for i in range(3):
            print(f"\nQuery {i+1}:")
            for row in connector.execute_query("SELECT version()"):
                print(f"  {row}")

    finally:
        connector.disconnect()


def example_ssl_connection():
    """Secure SSL connection."""
    print("\n=== Example 10: SSL Connection ===")

    pg_config = PostgresConfig(
        host="secure-postgres.example.com",
        database="production",
        username="prod_user",
        password="secure_password",
        sslmode="require",  # Require SSL
        connect_timeout=30
    )

    source_config = SourceConnectionConfig(
        name="production_db",
        source_type=SourceType.DATABASE,
        description="Production database with SSL"
    )

    try:
        with PostgresConnector(source_config, pg_config) as conn:
            # Test connection
            if conn.test_connection():
                print("✓ Secure SSL connection established")

                info = conn.get_connection_info()
                print(f"  SSL Mode: {info['sslmode']}")
                print(f"  Host: {info['host']}")

    except Exception as e:
        print(f"Connection failed: {e}")


def main():
    """Run all examples."""
    examples = [
        example_basic_connection,
        example_context_manager,
        example_connection_string,
        example_schema_introspection,
        example_parameterized_queries,
        example_transactions,
        example_streaming_large_results,
        example_multiple_schemas,
        example_connection_pooling,
        example_ssl_connection,
    ]

    print("PostgreSQL Connector Examples")
    print("=" * 60)

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Example failed: {e}")
            print("(This is expected if PostgreSQL is not running)")

    print("\n" + "=" * 60)
    print("Examples complete!")


if __name__ == "__main__":
    main()
