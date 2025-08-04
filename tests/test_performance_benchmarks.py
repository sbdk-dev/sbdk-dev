"""
Performance Benchmarking Test Suite for SBDK.dev v2.0.0
Comprehensive performance testing and benchmarking
"""

import json
import os
import tempfile
import threading
import time
from pathlib import Path

import duckdb
import pandas as pd
import psutil
import pytest
from typer.testing import CliRunner

from sbdk.cli.commands.run import load_config
from sbdk.cli.main import app
from sbdk.templates.pipelines.events import generate_events_data
from sbdk.templates.pipelines.orders import generate_orders_data
from sbdk.templates.pipelines.users import generate_users_data


class PerformanceMetrics:
    """Helper class for collecting performance metrics"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process()

    def start(self):
        """Start performance measurement"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    def stop(self):
        """Stop performance measurement"""
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    @property
    def execution_time(self):
        """Get execution time in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def memory_usage(self):
        """Get memory usage difference in MB"""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return None


@pytest.mark.performance
class TestCLIPerformance:
    """Test CLI command performance"""

    def test_help_command_performance(self):
        """Test help command response time"""
        metrics = PerformanceMetrics()
        runner = CliRunner()

        metrics.start()
        result = runner.invoke(app, ["--help"])
        metrics.stop()

        assert result.exit_code == 0
        assert metrics.execution_time < 1.0  # Should be very fast
        print(f"Help command took {metrics.execution_time:.3f}s")

    def test_init_command_performance(self):
        """Test project initialization performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            metrics = PerformanceMetrics()
            runner = CliRunner()

            metrics.start()
            result = runner.invoke(app, ["init", "perf_test_project"])
            metrics.stop()

            assert result.exit_code == 0
            assert metrics.execution_time < 3.0  # Should init quickly
            print(
                f"Init command took {metrics.execution_time:.3f}s, used {metrics.memory_usage:.1f}MB"
            )

    def test_config_loading_performance(self):
        """Test configuration loading performance with various sizes"""
        test_cases = [
            ("small", {"project": "test", "target": "dev"}),
            ("medium", {"project": "test", "data": list(range(1000))}),
            (
                "large",
                {
                    "project": "test",
                    "data": list(range(10000)),
                    "config": {f"key_{i}": f"value_{i}" for i in range(1000)},
                },
            ),
        ]

        for size, config_data in test_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)

                with open("sbdk_config.json", "w") as f:
                    json.dump(config_data, f)

                metrics = PerformanceMetrics()

                metrics.start()
                config = load_config()
                metrics.stop()

                assert config["project"] == "test"
                assert metrics.execution_time < 0.5  # Should load quickly
                print(f"Config loading ({size}) took {metrics.execution_time:.3f}s")


@pytest.mark.performance
class TestDataGenerationPerformance:
    """Test data generation performance"""

    def test_users_generation_scalability(self):
        """Test user data generation at different scales"""
        scales = [100, 1000, 5000, 10000]

        for scale in scales:
            metrics = PerformanceMetrics()

            metrics.start()
            users = generate_users_data(scale)
            metrics.stop()

            assert len(users) == scale

            # Performance expectations
            if scale <= 1000:
                assert metrics.execution_time < 1.0
            elif scale <= 5000:
                assert metrics.execution_time < 3.0
            else:
                assert metrics.execution_time < 10.0

            print(
                f"Generated {scale} users in {metrics.execution_time:.3f}s ({scale/metrics.execution_time:.0f} users/sec)"
            )

    def test_events_generation_scalability(self):
        """Test event data generation at different scales"""
        scales = [1000, 5000, 10000, 50000]

        for scale in scales:
            metrics = PerformanceMetrics()

            metrics.start()
            events = generate_events_data(scale, max_user_id=1000)
            metrics.stop()

            assert len(events) == scale

            # Performance expectations
            if scale <= 5000:
                assert metrics.execution_time < 2.0
            elif scale <= 10000:
                assert metrics.execution_time < 5.0
            else:
                assert metrics.execution_time < 30.0  # Increased timeout for CI

            print(
                f"Generated {scale} events in {metrics.execution_time:.3f}s ({scale/metrics.execution_time:.0f} events/sec)"
            )

    def test_orders_generation_scalability(self):
        """Test order data generation at different scales"""
        scales = [500, 2000, 5000, 10000]

        for scale in scales:
            metrics = PerformanceMetrics()

            metrics.start()
            orders = generate_orders_data(scale, max_user_id=1000)
            metrics.stop()

            assert len(orders) == scale

            # Performance expectations
            if scale <= 2000:
                assert metrics.execution_time < 1.0
            elif scale <= 5000:
                assert metrics.execution_time < 3.0
            else:
                assert metrics.execution_time < 8.0

            print(
                f"Generated {scale} orders in {metrics.execution_time:.3f}s ({scale/metrics.execution_time:.0f} orders/sec)"
            )


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database operations performance"""

    def test_duckdb_creation_performance(self):
        """Test DuckDB database creation and insertion performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Test database creation
            metrics = PerformanceMetrics()

            metrics.start()
            con = duckdb.connect("perf_test.duckdb")
            metrics.stop()

            assert metrics.execution_time < 1.0  # Allow more time for CI environments
            print(f"Database creation took {metrics.execution_time:.3f}s")

            # Test large data insertion
            large_dataset = generate_users_data(10000)
            pd.DataFrame(large_dataset)

            metrics.start()
            con.execute("CREATE TABLE users AS SELECT * FROM df")
            metrics.stop()

            # Verify data
            count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            assert count == 10000
            assert metrics.execution_time < 5.0  # Should insert quickly

            print(
                f"Inserted 10k records in {metrics.execution_time:.3f}s ({10000/metrics.execution_time:.0f} records/sec)"
            )

            con.close()

    def test_duckdb_query_performance(self):
        """Test DuckDB query performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Create test database
            con = duckdb.connect("query_perf.duckdb")

            # Insert test data
            users = generate_users_data(50000)
            events = generate_events_data(200000, max_user_id=50000)

            pd.DataFrame(users)
            pd.DataFrame(events)

            con.execute("CREATE TABLE users AS SELECT * FROM users_df")
            con.execute("CREATE TABLE events AS SELECT * FROM events_df")

            # Test various query types
            queries = [
                ("Simple SELECT", "SELECT COUNT(*) FROM users"),
                (
                    "JOIN query",
                    "SELECT COUNT(*) FROM users u JOIN events e ON u.user_id = e.user_id",
                ),
                (
                    "Aggregation",
                    "SELECT subscription_tier, COUNT(*) FROM users GROUP BY subscription_tier",
                ),
                (
                    "Complex query",
                    """
                    SELECT u.subscription_tier, COUNT(*) as event_count, AVG(u.user_id) as avg_user_id
                    FROM users u
                    JOIN events e ON u.user_id = e.user_id
                    WHERE u.created_at > '2023-01-01'
                    GROUP BY u.subscription_tier
                    ORDER BY event_count DESC
                """,
                ),
            ]

            for query_name, query in queries:
                metrics = PerformanceMetrics()

                metrics.start()
                result = con.execute(query).fetchall()
                metrics.stop()

                assert len(result) > 0
                assert metrics.execution_time < 2.0  # Should be fast

                print(f"{query_name} took {metrics.execution_time:.3f}s")

            con.close()


@pytest.mark.performance
class TestConcurrencyPerformance:
    """Test concurrent operations performance"""

    def test_parallel_data_generation(self):
        """Test parallel data generation performance"""
        import concurrent.futures

        def generate_dataset(dataset_type, size):
            start_time = time.time()
            if dataset_type == "users":
                data = generate_users_data(size)
            elif dataset_type == "events":
                data = generate_events_data(size, max_user_id=1000)
            else:  # orders
                data = generate_orders_data(size, max_user_id=1000)
            end_time = time.time()
            return dataset_type, len(data), end_time - start_time

        metrics = PerformanceMetrics()

        # Test parallel execution
        metrics.start()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(generate_dataset, "users", 5000),
                executor.submit(generate_dataset, "events", 20000),
                executor.submit(generate_dataset, "orders", 10000),
            ]

            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]
        metrics.stop()

        # Verify all datasets generated
        total_records = sum(result[1] for result in results)
        assert total_records == 35000

        print(f"Parallel generation of 35k records took {metrics.execution_time:.3f}s")

        # Compare with sequential execution
        metrics_seq = PerformanceMetrics()
        metrics_seq.start()
        seq_users = generate_users_data(5000)
        seq_events = generate_events_data(20000, max_user_id=1000)
        seq_orders = generate_orders_data(10000, max_user_id=1000)
        metrics_seq.stop()

        assert len(seq_users) + len(seq_events) + len(seq_orders) == 35000
        print(f"Sequential generation took {metrics_seq.execution_time:.3f}s")

        # Parallel should be faster (or at least not significantly slower due to GIL)
        speedup = metrics_seq.execution_time / metrics.execution_time
        print(f"Speedup: {speedup:.2f}x")

    def test_multiple_cli_instances_performance(self):
        """Test performance with multiple CLI instances"""
        import queue

        results = queue.Queue()

        def run_cli_command(command_args, temp_dir):
            os.chdir(temp_dir)
            runner = CliRunner()

            start_time = time.time()
            result = runner.invoke(app, command_args)
            end_time = time.time()

            results.put((command_args[0], result.exit_code, end_time - start_time))

        # Create temp directories for each instance
        temp_dirs = []
        for i in range(5):
            temp_dir = tempfile.mkdtemp()
            temp_dirs.append(temp_dir)

        try:
            metrics = PerformanceMetrics()

            # Start multiple CLI instances
            metrics.start()
            threads = []
            for i in range(5):
                thread = threading.Thread(
                    target=run_cli_command,
                    args=(["init", f"concurrent_project_{i}"], temp_dirs[i]),
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()
            metrics.stop()

            # Collect results
            successful = 0
            total_time = 0
            while not results.empty():
                command, exit_code, execution_time = results.get()
                if exit_code == 0:
                    successful += 1
                total_time += execution_time

            assert successful == 5
            print(
                f"5 concurrent CLI instances took {metrics.execution_time:.3f}s total"
            )
            print(f"Average per instance: {total_time/5:.3f}s")

        finally:
            # Cleanup temp directories
            import shutil

            for temp_dir in temp_dirs:
                shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.performance
class TestMemoryPerformance:
    """Test memory usage and efficiency"""

    def test_memory_usage_large_datasets(self):
        """Test memory usage with large datasets"""
        import tracemalloc

        tracemalloc.start()

        # Generate large datasets
        large_users = generate_users_data(20000)
        current, peak = tracemalloc.get_traced_memory()
        users_memory = current / 1024 / 1024  # MB

        large_events = generate_events_data(100000, max_user_id=20000)
        current, peak = tracemalloc.get_traced_memory()
        events_memory = current / 1024 / 1024  # MB

        large_orders = generate_orders_data(50000, max_user_id=20000)
        current, peak = tracemalloc.get_traced_memory()
        total_memory = current / 1024 / 1024  # MB

        tracemalloc.stop()

        # Verify data generated
        assert len(large_users) == 20000
        assert len(large_events) == 100000
        assert len(large_orders) == 50000

        # Memory usage should be reasonable
        assert total_memory < 500  # Less than 500MB

        print(
            f"Memory usage - Users: {users_memory:.1f}MB, Events: {events_memory:.1f}MB, Total: {total_memory:.1f}MB"
        )

    def test_memory_cleanup_after_operations(self):
        """Test memory cleanup after operations"""
        import gc

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Perform memory-intensive operations
        for _i in range(10):
            data = generate_users_data(5000)
            del data
            gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        # Memory increase should be minimal after cleanup
        assert memory_increase < 100  # Allow more memory variance in CI

        print(f"Memory increase after 10 operations: {memory_increase:.1f}MB")


@pytest.mark.performance
class TestScalabilityLimits:
    """Test scalability limits and breaking points"""

    @pytest.mark.slow
    def test_maximum_dataset_size(self):
        """Test maximum practical dataset sizes"""
        # This test is marked as slow and tests limits
        max_sizes = {"users": 100000, "events": 500000, "orders": 200000}

        for dataset_type, max_size in max_sizes.items():
            metrics = PerformanceMetrics()

            try:
                metrics.start()
                if dataset_type == "users":
                    data = generate_users_data(max_size)
                elif dataset_type == "events":
                    data = generate_events_data(max_size, max_user_id=10000)
                else:
                    data = generate_orders_data(max_size, max_user_id=10000)
                metrics.stop()

                assert len(data) == max_size
                assert (
                    metrics.execution_time < 120
                )  # Allow more time for large datasets in CI

                print(
                    f"Generated {max_size} {dataset_type} in {metrics.execution_time:.1f}s"
                )

            except MemoryError:
                pytest.skip(f"Insufficient memory for {max_size} {dataset_type}")
            except Exception as e:
                pytest.fail(f"Failed to generate {max_size} {dataset_type}: {e}")

    def test_database_size_limits(self):
        """Test database size handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            con = duckdb.connect("scale_test.duckdb")

            # Insert data in batches
            total_records = 0
            batch_size = 10000
            max_batches = 10

            for batch in range(max_batches):
                users = generate_users_data(batch_size)
                pd.DataFrame(users)

                if batch == 0:
                    con.execute("CREATE TABLE scale_users AS SELECT * FROM df")
                else:
                    con.execute("INSERT INTO scale_users SELECT * FROM df")

                total_records += batch_size

                # Check database size
                db_size = Path("scale_test.duckdb").stat().st_size / 1024 / 1024  # MB

                print(
                    f"Batch {batch + 1}: {total_records} records, DB size: {db_size:.1f}MB"
                )

            # Verify final count
            final_count = con.execute("SELECT COUNT(*) FROM scale_users").fetchone()[0]
            assert final_count == total_records

            con.close()


if __name__ == "__main__":
    # Run performance tests with detailed output
    pytest.main([__file__, "-v", "-s", "-m", "performance"])
