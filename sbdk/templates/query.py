#!/usr/bin/env python3
"""
DuckDB Query Helper for SBDK Projects

This script provides easy access to your SBDK project's DuckDB database.
Since DuckDB is installed as a Python package, you can query your data
without installing the standalone DuckDB CLI.

Usage:
    python query.py                          # Show all tables
    python query.py "SELECT * FROM users"    # Run SQL query
    python query.py --interactive            # Interactive mode

Installation of DuckDB CLI (optional):
    macOS:   brew install duckdb
    Linux:   See https://duckdb.org/docs/installation/
    Windows: See https://duckdb.org/docs/installation/
"""
import sys
import argparse
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("❌ DuckDB not found. Install with: pip install duckdb")
    sys.exit(1)


def find_database():
    """Find the DuckDB database file in the project"""
    # Look for .duckdb files in data directory
    data_dir = Path("data")
    if data_dir.exists():
        db_files = list(data_dir.glob("*.duckdb"))
        if db_files:
            return db_files[0]

    # Look for any .duckdb file
    db_files = list(Path(".").glob("**/*.duckdb"))
    if db_files:
        return db_files[0]

    return None


def show_tables(conn):
    """Display all tables with row counts"""
    print("\n📊 Available Tables:")
    print("=" * 70)

    tables = conn.execute("SHOW TABLES").fetchall()
    if not tables:
        print("  No tables found. Run 'sbdk run' to generate data.")
        return

    total_rows = 0
    for table in tables:
        table_name = table[0]
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        total_rows += row_count
        print(f"  📋 {table_name:<30} {row_count:>12,} rows")

    print("=" * 70)
    print(f"  Total rows across all tables: {total_rows:,}\n")


def execute_query(conn, query):
    """Execute a SQL query and display results"""
    print(f"\n🔍 Executing: {query}\n")
    print("=" * 70)

    try:
        result = conn.execute(query).fetchdf()
        if result.empty:
            print("  No results returned.")
        else:
            print(result.to_string(index=False))
            print("=" * 70)
            print(f"✅ Returned {len(result)} row(s)\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
        sys.exit(1)


def interactive_mode(conn):
    """Interactive SQL prompt"""
    print("\n🔄 Interactive Mode")
    print("=" * 70)
    print("Enter SQL queries (type 'exit', 'quit', or Ctrl+D to exit)")
    print("Type 'tables' to show all tables")
    print("=" * 70 + "\n")

    while True:
        try:
            query = input("duckdb> ").strip()

            if not query:
                continue

            if query.lower() in ('exit', 'quit', 'q'):
                print("👋 Goodbye!")
                break

            if query.lower() == 'tables':
                show_tables(conn)
                continue

            execute_query(conn, query)

        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Query your SBDK project's DuckDB database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query.py                                    # Show all tables
  python query.py "SELECT * FROM stg_users LIMIT 5"  # Run query
  python query.py -i                                 # Interactive mode
  python query.py -f queries.sql                     # Run from file

Common Queries:
  python query.py "SHOW TABLES"
  python query.py "SELECT COUNT(*) FROM stg_orders"
  python query.py "SELECT * FROM user_metrics LIMIT 10"
        """
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='SQL query to execute'
    )

    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Start interactive mode'
    )

    parser.add_argument(
        '-f', '--file',
        type=Path,
        help='Execute SQL from file'
    )

    parser.add_argument(
        '--db',
        type=Path,
        help='Path to DuckDB database file'
    )

    args = parser.parse_args()

    # Find database
    db_path = args.db if args.db else find_database()

    if not db_path or not Path(db_path).exists():
        print("❌ Database not found!")
        print("\n💡 Possible solutions:")
        print("   1. Run 'sbdk run' to create the database")
        print("   2. Specify database path with --db option")
        print("   3. Check that you're in an SBDK project directory")
        sys.exit(1)

    print(f"📂 Using database: {db_path}")

    # Connect to database
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

    try:
        # Execute from file
        if args.file:
            if not args.file.exists():
                print(f"❌ File not found: {args.file}")
                sys.exit(1)

            with open(args.file) as f:
                query = f.read()
            execute_query(conn, query)

        # Interactive mode
        elif args.interactive:
            interactive_mode(conn)

        # Single query
        elif args.query:
            execute_query(conn, args.query)

        # Default: show tables
        else:
            show_tables(conn)
            print("💡 Run with -h for more options")
            print("   Example: python query.py \"SELECT * FROM stg_users LIMIT 5\"")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
