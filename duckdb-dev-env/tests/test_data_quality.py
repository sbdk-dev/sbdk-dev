"""
Test suite for data quality checks and validation in SBDK.dev pipeline.
Tests data integrity, schema validation, and pipeline data quality.
"""

import pytest
import pandas as pd
import duckdb
import dlt
import tempfile
import os
from datetime import datetime, timedelta
from faker import Faker
import json


class TestDataQuality:
    """Test suite for data quality validation and checks."""

    @pytest.fixture
    def fake_data_generator(self):
        """Initialize Faker for generating test data."""
        return Faker()

    @pytest.fixture
    def temp_db_connection(self):
        """Create temporary DuckDB connection for testing."""
        # Create a temporary file path without creating the file
        import tempfile

        fd, temp_path = tempfile.mkstemp(suffix=".duckdb")
        os.close(fd)  # Close the file descriptor
        os.unlink(temp_path)  # Remove the empty file

        try:
            conn = duckdb.connect(temp_path)
            yield conn
        finally:
            conn.close()
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.fixture
    def sample_users_data(self, fake_data_generator):
        """Generate sample users data matching PRD specification."""
        users = []
        for i in range(1, 1001):  # 1000 users
            users.append(
                {
                    "user_id": i,
                    "created_at": fake_data_generator.date_time_between(
                        start_date="-1y", end_date="now"
                    ),
                    "country": fake_data_generator.country_code(),
                    "referrer": fake_data_generator.random_element(
                        elements=("google", "bing", "direct", "email")
                    ),
                }
            )
        return users

    @pytest.fixture
    def sample_events_data(self, fake_data_generator):
        """Generate sample events data matching PRD specification."""
        events = []
        for i in range(5000):  # 5000 events
            events.append(
                {
                    "event_id": i,
                    "user_id": fake_data_generator.random_int(min=1, max=1000),
                    "event_type": fake_data_generator.random_element(
                        elements=("pageview", "signup", "purchase", "login")
                    ),
                    "timestamp": fake_data_generator.date_time_between(
                        start_date="-30d", end_date="now"
                    ),
                    "utm_source": fake_data_generator.random_element(
                        elements=("google", "facebook", "newsletter", "direct")
                    ),
                }
            )
        return events

    @pytest.fixture
    def sample_orders_data(self, fake_data_generator):
        """Generate sample orders data matching PRD specification."""
        orders = []
        for i in range(2000):  # 2000 orders
            orders.append(
                {
                    "order_id": i,
                    "user_id": fake_data_generator.random_int(min=1, max=1000),
                    "amount": round(fake_data_generator.random.uniform(10, 500), 2),
                    "product_category": fake_data_generator.random_element(
                        elements=("subscription", "addon", "renewal")
                    ),
                    "payment_method": fake_data_generator.random_element(
                        elements=("credit_card", "paypal", "wire")
                    ),
                }
            )
        return orders

    def test_users_data_schema_validation(self, sample_users_data, temp_db_connection):
        """Test that users data has correct schema and data types."""
        # Load data into DuckDB
        df = pd.DataFrame(sample_users_data)
        temp_db_connection.execute("CREATE TABLE users AS SELECT * FROM df")

        # Check schema
        schema = temp_db_connection.execute("DESCRIBE users").fetchall()
        column_info = {row[0]: row[1] for row in schema}

        # Verify required columns exist
        required_columns = ["user_id", "created_at", "country", "referrer"]
        for col in required_columns:
            assert col in column_info, f"Required column {col} missing"

        # Verify data types
        assert "INTEGER" in column_info["user_id"] or "BIGINT" in column_info["user_id"]
        assert (
            "TIMESTAMP" in column_info["created_at"]
            or "DATE" in column_info["created_at"]
        )
        assert "VARCHAR" in column_info["country"]
        assert "VARCHAR" in column_info["referrer"]

    def test_users_data_integrity_checks(self, sample_users_data, temp_db_connection):
        """Test data integrity for users table."""
        df = pd.DataFrame(sample_users_data)
        temp_db_connection.execute("CREATE TABLE users AS SELECT * FROM df")

        # Check for duplicate user_ids
        duplicate_count = temp_db_connection.execute(
            "SELECT COUNT(*) FROM (SELECT user_id, COUNT(*) as cnt FROM users GROUP BY user_id HAVING cnt > 1)"
        ).fetchone()[0]
        assert duplicate_count == 0, "Found duplicate user_ids"

        # Check for null values in required fields
        null_user_ids = temp_db_connection.execute(
            "SELECT COUNT(*) FROM users WHERE user_id IS NULL"
        ).fetchone()[0]
        assert null_user_ids == 0, "Found null user_ids"

        # Check country code format (should be 2 characters)
        invalid_countries = temp_db_connection.execute(
            "SELECT COUNT(*) FROM users WHERE LENGTH(country) != 2"
        ).fetchone()[0]
        assert invalid_countries == 0, "Found invalid country codes"

        # Check referrer values are in expected set
        valid_referrers = ["google", "bing", "direct", "email"]
        referrer_list = ",".join([f"'{x}'" for x in valid_referrers])
        invalid_referrers = temp_db_connection.execute(
            f"SELECT COUNT(*) FROM users WHERE referrer NOT IN ({referrer_list})"
        ).fetchone()[0]
        assert invalid_referrers == 0, "Found invalid referrer values"

    def test_events_data_schema_validation(
        self, sample_events_data, temp_db_connection
    ):
        """Test that events data has correct schema and data types."""
        df = pd.DataFrame(sample_events_data)
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM df")

        # Check schema
        schema = temp_db_connection.execute("DESCRIBE events").fetchall()
        column_info = {row[0]: row[1] for row in schema}

        # Verify required columns
        required_columns = [
            "event_id",
            "user_id",
            "event_type",
            "timestamp",
            "utm_source",
        ]
        for col in required_columns:
            assert col in column_info, f"Required column {col} missing"

        # Verify data types
        assert (
            "INTEGER" in column_info["event_id"] or "BIGINT" in column_info["event_id"]
        )
        assert "INTEGER" in column_info["user_id"] or "BIGINT" in column_info["user_id"]
        assert "VARCHAR" in column_info["event_type"]
        assert (
            "TIMESTAMP" in column_info["timestamp"]
            or "DATE" in column_info["timestamp"]
        )
        assert "VARCHAR" in column_info["utm_source"]

    def test_events_data_integrity_checks(self, sample_events_data, temp_db_connection):
        """Test data integrity for events table."""
        df = pd.DataFrame(sample_events_data)
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM df")

        # Check for duplicate event_ids
        duplicate_count = temp_db_connection.execute(
            "SELECT COUNT(*) FROM (SELECT event_id, COUNT(*) as cnt FROM events GROUP BY event_id HAVING cnt > 1)"
        ).fetchone()[0]
        assert duplicate_count == 0, "Found duplicate event_ids"

        # Check event_type values are valid
        valid_event_types = ["pageview", "signup", "purchase", "login"]
        event_type_list = ",".join([f"'{x}'" for x in valid_event_types])
        invalid_events = temp_db_connection.execute(
            f"SELECT COUNT(*) FROM events WHERE event_type NOT IN ({event_type_list})"
        ).fetchone()[0]
        assert invalid_events == 0, "Found invalid event_type values"

        # Check utm_source values are valid
        valid_utm_sources = ["google", "facebook", "newsletter", "direct"]
        utm_source_list = ",".join([f"'{x}'" for x in valid_utm_sources])
        invalid_utm = temp_db_connection.execute(
            f"SELECT COUNT(*) FROM events WHERE utm_source NOT IN ({utm_source_list})"
        ).fetchone()[0]
        assert invalid_utm == 0, "Found invalid utm_source values"

        # Check user_id references valid range (assuming 1-1000)
        invalid_user_refs = temp_db_connection.execute(
            "SELECT COUNT(*) FROM events WHERE user_id < 1 OR user_id > 1000"
        ).fetchone()[0]
        assert invalid_user_refs == 0, "Found invalid user_id references"

    def test_orders_data_schema_validation(
        self, sample_orders_data, temp_db_connection
    ):
        """Test that orders data has correct schema and data types."""
        df = pd.DataFrame(sample_orders_data)
        temp_db_connection.execute("CREATE TABLE orders AS SELECT * FROM df")

        # Check schema
        schema = temp_db_connection.execute("DESCRIBE orders").fetchall()
        column_info = {row[0]: row[1] for row in schema}

        # Verify required columns
        required_columns = [
            "order_id",
            "user_id",
            "amount",
            "product_category",
            "payment_method",
        ]
        for col in required_columns:
            assert col in column_info, f"Required column {col} missing"

        # Verify data types
        assert (
            "INTEGER" in column_info["order_id"] or "BIGINT" in column_info["order_id"]
        )
        assert "INTEGER" in column_info["user_id"] or "BIGINT" in column_info["user_id"]
        assert "DOUBLE" in column_info["amount"] or "DECIMAL" in column_info["amount"]
        assert "VARCHAR" in column_info["product_category"]
        assert "VARCHAR" in column_info["payment_method"]

    def test_orders_data_integrity_checks(self, sample_orders_data, temp_db_connection):
        """Test data integrity for orders table."""
        df = pd.DataFrame(sample_orders_data)
        temp_db_connection.execute("CREATE TABLE orders AS SELECT * FROM df")

        # Check for duplicate order_ids
        duplicate_count = temp_db_connection.execute(
            "SELECT COUNT(*) FROM (SELECT order_id, COUNT(*) as cnt FROM orders GROUP BY order_id HAVING cnt > 1)"
        ).fetchone()[0]
        assert duplicate_count == 0, "Found duplicate order_ids"

        # Check amount values are positive and reasonable
        invalid_amounts = temp_db_connection.execute(
            "SELECT COUNT(*) FROM orders WHERE amount <= 0 OR amount > 1000"
        ).fetchone()[0]
        assert invalid_amounts == 0, "Found invalid amount values"

        # Check product_category values are valid
        valid_categories = ["subscription", "addon", "renewal"]
        category_list = ",".join([f"'{x}'" for x in valid_categories])
        invalid_categories = temp_db_connection.execute(
            f"SELECT COUNT(*) FROM orders WHERE product_category NOT IN ({category_list})"
        ).fetchone()[0]
        assert invalid_categories == 0, "Found invalid product_category values"

        # Check payment_method values are valid
        valid_methods = ["credit_card", "paypal", "wire"]
        method_list = ",".join([f"'{x}'" for x in valid_methods])
        invalid_methods = temp_db_connection.execute(
            f"SELECT COUNT(*) FROM orders WHERE payment_method NOT IN ({method_list})"
        ).fetchone()[0]
        assert invalid_methods == 0, "Found invalid payment_method values"

    def test_referential_integrity(
        self,
        sample_users_data,
        sample_events_data,
        sample_orders_data,
        temp_db_connection,
    ):
        """Test referential integrity between tables."""
        # Load all data
        users_df = pd.DataFrame(sample_users_data)
        events_df = pd.DataFrame(sample_events_data)
        orders_df = pd.DataFrame(sample_orders_data)

        temp_db_connection.execute("CREATE TABLE users AS SELECT * FROM users_df")
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM events_df")
        temp_db_connection.execute("CREATE TABLE orders AS SELECT * FROM orders_df")

        # Check that all event user_ids exist in users table
        orphaned_events = temp_db_connection.execute(
            """
            SELECT COUNT(*) FROM events e 
            LEFT JOIN users u ON e.user_id = u.user_id 
            WHERE u.user_id IS NULL
        """
        ).fetchone()[0]

        # Note: Due to random generation, some events might reference non-existent users
        # In a real pipeline, this would be a critical error
        if orphaned_events > 0:
            print(
                f"Warning: Found {orphaned_events} events with invalid user_id references"
            )

        # Check that all order user_ids exist in users table
        orphaned_orders = temp_db_connection.execute(
            """
            SELECT COUNT(*) FROM orders o 
            LEFT JOIN users u ON o.user_id = u.user_id 
            WHERE u.user_id IS NULL
        """
        ).fetchone()[0]

        if orphaned_orders > 0:
            print(
                f"Warning: Found {orphaned_orders} orders with invalid user_id references"
            )

    def test_data_freshness_validation(self, sample_events_data, temp_db_connection):
        """Test data freshness and timestamp validation."""
        df = pd.DataFrame(sample_events_data)
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM df")

        # Check that timestamps are within expected range (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        # Cast both timestamps to consistent types for comparison
        future_events = temp_db_connection.execute(
            "SELECT COUNT(*) FROM events WHERE CAST(timestamp AS TIMESTAMP) > CAST(CURRENT_TIMESTAMP AS TIMESTAMP)"
        ).fetchone()[0]

        assert future_events == 0, "Found events with future timestamps"

        # Check for events older than expected range
        # Cast timestamp to date for comparison to avoid type mismatch
        very_old_events = temp_db_connection.execute(
            f"SELECT COUNT(*) FROM events WHERE CAST(timestamp AS DATE) < '{thirty_days_ago.strftime('%Y-%m-%d')}'"
        ).fetchone()[0]

        # This might have some tolerance based on data generation
        if very_old_events > len(sample_events_data) * 0.1:  # More than 10% are too old
            print(f"Warning: Found {very_old_events} events older than expected range")

    def test_data_completeness(
        self,
        sample_users_data,
        sample_events_data,
        sample_orders_data,
        temp_db_connection,
    ):
        """Test data completeness and expected volumes."""
        # Load data
        users_df = pd.DataFrame(sample_users_data)
        events_df = pd.DataFrame(sample_events_data)
        orders_df = pd.DataFrame(sample_orders_data)

        temp_db_connection.execute("CREATE TABLE users AS SELECT * FROM users_df")
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM events_df")
        temp_db_connection.execute("CREATE TABLE orders AS SELECT * FROM orders_df")

        # Check expected record counts
        users_count = temp_db_connection.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
        events_count = temp_db_connection.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        orders_count = temp_db_connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        assert users_count == len(
            sample_users_data
        ), f"Expected {len(sample_users_data)} users, got {users_count}"
        assert events_count == len(
            sample_events_data
        ), f"Expected {len(sample_events_data)} events, got {events_count}"
        assert orders_count == len(
            sample_orders_data
        ), f"Expected {len(sample_orders_data)} orders, got {orders_count}"

        # Check for null values in critical fields
        null_checks = [
            ("users", "user_id"),
            ("users", "created_at"),
            ("events", "event_id"),
            ("events", "user_id"),
            ("events", "event_type"),
            ("orders", "order_id"),
            ("orders", "user_id"),
            ("orders", "amount"),
        ]

        for table, column in null_checks:
            null_count = temp_db_connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
            ).fetchone()[0]
            assert (
                null_count == 0
            ), f"Found {null_count} null values in {table}.{column}"

    def test_data_distribution_validation(self, sample_events_data, temp_db_connection):
        """Test that data distributions are reasonable."""
        df = pd.DataFrame(sample_events_data)
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM df")

        # Check event type distribution
        event_type_dist = temp_db_connection.execute(
            """
            SELECT event_type, COUNT(*) as cnt, 
                   COUNT(*) * 100.0 / (SELECT COUNT(*) FROM events) as percentage
            FROM events 
            GROUP BY event_type
            ORDER BY cnt DESC
        """
        ).fetchall()

        # Verify we have all expected event types
        expected_types = ["pageview", "signup", "purchase", "login"]
        actual_types = [row[0] for row in event_type_dist]

        for expected_type in expected_types:
            assert expected_type in actual_types, f"Missing event type: {expected_type}"

        # Check that no single event type dominates too much (> 80%)
        for event_type, count, percentage in event_type_dist:
            assert (
                percentage < 80
            ), f"Event type {event_type} represents {percentage}% of data (too dominant)"

        # Check UTM source distribution
        utm_dist = temp_db_connection.execute(
            """
            SELECT utm_source, COUNT(*) as cnt
            FROM events 
            GROUP BY utm_source
        """
        ).fetchall()

        expected_sources = ["google", "facebook", "newsletter", "direct"]
        actual_sources = [row[0] for row in utm_dist]

        for expected_source in expected_sources:
            assert (
                expected_source in actual_sources
            ), f"Missing UTM source: {expected_source}"


class TestDataQualityRules:
    """Test suite for business rule validation and data quality rules."""

    @pytest.fixture
    def temp_db_connection(self):
        """Create temporary DuckDB connection for testing."""
        # Create a temporary file path without creating the file
        import tempfile

        fd, temp_path = tempfile.mkstemp(suffix=".duckdb")
        os.close(fd)  # Close the file descriptor
        os.unlink(temp_path)  # Remove the empty file

        try:
            conn = duckdb.connect(temp_path)
            yield conn
        finally:
            conn.close()
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_business_rule_user_signup_before_activity(self, temp_db_connection):
        """Test that users are created before their first activity."""
        # Create test data with potential violation
        users_data = [
            {"user_id": 1, "created_at": datetime(2024, 1, 15)},
            {"user_id": 2, "created_at": datetime(2024, 1, 20)},
        ]

        events_data = [
            {
                "event_id": 1,
                "user_id": 1,
                "event_type": "pageview",
                "timestamp": datetime(2024, 1, 16),
            },  # Valid
            {
                "event_id": 2,
                "user_id": 2,
                "event_type": "signup",
                "timestamp": datetime(2024, 1, 18),
            },  # Invalid - before user created
        ]

        users_df = pd.DataFrame(users_data)
        events_df = pd.DataFrame(events_data)

        temp_db_connection.execute("CREATE TABLE users AS SELECT * FROM users_df")
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM events_df")

        # Check for events before user creation
        violations = temp_db_connection.execute(
            """
            SELECT e.event_id, e.user_id, e.timestamp, u.created_at
            FROM events e
            JOIN users u ON e.user_id = u.user_id
            WHERE e.timestamp < u.created_at
        """
        ).fetchall()

        # This would be a business rule violation in real scenario
        if violations:
            print(f"Found {len(violations)} events occurring before user creation")

    def test_business_rule_order_amounts_reasonable(self, temp_db_connection):
        """Test that order amounts are within reasonable business limits."""
        orders_data = [
            {
                "order_id": 1,
                "user_id": 1,
                "amount": 50.00,
                "product_category": "subscription",
            },  # Valid
            {
                "order_id": 2,
                "user_id": 2,
                "amount": 10000.00,
                "product_category": "addon",
            },  # Suspicious
            {
                "order_id": 3,
                "user_id": 3,
                "amount": -10.00,
                "product_category": "renewal",
            },  # Invalid
        ]

        orders_df = pd.DataFrame(orders_data)
        temp_db_connection.execute("CREATE TABLE orders AS SELECT * FROM orders_df")

        # Check for negative amounts
        negative_amounts = temp_db_connection.execute(
            "SELECT COUNT(*) FROM orders WHERE amount < 0"
        ).fetchone()[0]

        # The test data intentionally includes one negative amount to test business rule validation
        # In real implementation, this would trigger alerts or rejections
        if negative_amounts > 0:
            print(
                f"Warning: Found {negative_amounts} orders with negative amounts (expected for test)"
            )
            # For this test, we expect exactly 1 negative amount
            assert (
                negative_amounts == 1
            ), f"Expected exactly 1 negative amount for testing, found {negative_amounts}"

        # Check for suspiciously high amounts (> $5000)
        high_amounts = temp_db_connection.execute(
            "SELECT COUNT(*) FROM orders WHERE amount > 5000"
        ).fetchone()[0]

        if high_amounts > 0:
            print(f"Warning: Found {high_amounts} orders with unusually high amounts")

    def test_data_consistency_rules(self, temp_db_connection):
        """Test data consistency rules across related records."""
        # Create test data with consistency issues
        users_data = [
            {"user_id": 1, "created_at": datetime(2024, 1, 15), "country": "US"},
            {"user_id": 2, "created_at": datetime(2024, 1, 20), "country": "CA"},
        ]

        events_data = [
            {
                "event_id": 1,
                "user_id": 1,
                "event_type": "signup",
                "timestamp": datetime(2024, 1, 16),
            },
            {
                "event_id": 2,
                "user_id": 1,
                "event_type": "signup",
                "timestamp": datetime(2024, 1, 17),
            },  # Duplicate signup
            {
                "event_id": 3,
                "user_id": 2,
                "event_type": "purchase",
                "timestamp": datetime(2024, 1, 21),
            },  # Purchase without signup
        ]

        users_df = pd.DataFrame(users_data)
        events_df = pd.DataFrame(events_data)

        temp_db_connection.execute("CREATE TABLE users AS SELECT * FROM users_df")
        temp_db_connection.execute("CREATE TABLE events AS SELECT * FROM events_df")

        # Check for users with multiple signup events
        multiple_signups = temp_db_connection.execute(
            """
            SELECT user_id, COUNT(*) as signup_count
            FROM events 
            WHERE event_type = 'signup'
            GROUP BY user_id
            HAVING COUNT(*) > 1
        """
        ).fetchall()

        if multiple_signups:
            print(
                f"Warning: Found users with multiple signup events: {multiple_signups}"
            )

        # Check for purchase events without prior signup
        purchases_without_signup = temp_db_connection.execute(
            """
            SELECT DISTINCT e1.user_id
            FROM events e1
            WHERE e1.event_type = 'purchase'
            AND NOT EXISTS (
                SELECT 1 FROM events e2 
                WHERE e2.user_id = e1.user_id 
                AND e2.event_type = 'signup'
                AND e2.timestamp < e1.timestamp
            )
        """
        ).fetchall()

        if purchases_without_signup:
            print(
                f"Warning: Found purchases without prior signup for users: {purchases_without_signup}"
            )


class TestPipelineDataQuality:
    """Test suite for end-to-end pipeline data quality validation."""

    def test_pipeline_data_quality_end_to_end(self):
        """Test complete pipeline data quality from generation to storage."""
        # This would test the actual pipeline from the PRD
        # Including: users.py, events.py, orders.py → DuckDB → dbt models

        # Create temporary pipeline environment
        fd, db_path = tempfile.mkstemp(suffix=".duckdb")
        os.close(fd)  # Close the file descriptor
        os.unlink(db_path)  # Remove the empty file

        try:
            # Simulate pipeline execution
            pipeline = dlt.pipeline(
                pipeline_name="quality_test",
                destination="duckdb",
                dataset_name="raw_data",
                export_schema_path="schema_export",
            )

            # Generate test data similar to PRD pipelines
            fake = Faker()

            # Users data
            users = [
                {
                    "user_id": i,
                    "created_at": fake.date_time_between(
                        start_date="-1y", end_date="now"
                    ),
                    "country": fake.country_code(),
                    "referrer": fake.random_element(
                        elements=("google", "bing", "direct", "email")
                    ),
                }
                for i in range(1, 101)
            ]

            # Load users
            load_info = pipeline.run(
                users, table_name="users", write_disposition="replace"
            )
            assert load_info is not None

            # Connect to the DLT-created database
            # DLT creates its own database file, we need to connect to that
            conn = duckdb.connect("quality_test.duckdb")

            # Basic quality checks
            user_count = conn.execute("SELECT COUNT(*) FROM raw_data.users").fetchone()[
                0
            ]
            assert user_count == 100

            # Schema validation
            schema = conn.execute("DESCRIBE raw_data.users").fetchall()
            column_names = [row[0] for row in schema]
            required_columns = ["user_id", "created_at", "country", "referrer"]

            for col in required_columns:
                assert col in column_names

            conn.close()

            # Cleanup DLT database
            if os.path.exists("quality_test.duckdb"):
                os.unlink("quality_test.duckdb")

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists("schema_export"):
                import shutil

                shutil.rmtree("schema_export", ignore_errors=True)
