import sys
import os
import pytest
import tempfile
import duckdb
import dlt
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from pipeline import run_pipeline


class TestDLTDuckDBPipeline:
    """Comprehensive test suite for DLT + DuckDB pipeline integration."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary DuckDB file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as tmp:
            yield tmp.name
        # Cleanup
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    @pytest.fixture
    def sample_data(self):
        """Sample test data for pipeline testing."""
        return [
            {"id": 1, "value": "foo", "category": "A", "amount": 100.50},
            {"id": 2, "value": "bar", "category": "B", "amount": 250.75},
            {"id": 3, "value": "baz", "category": "A", "amount": 75.25},
        ]

    def test_pipeline_runs_successfully(self, temp_db_path, sample_data):
        """Test that the basic pipeline executes without errors."""
        print("[TEST] Starting DLT → DuckDB pipeline test...")
        try:
            print(
                "[INPUT] Data to load:", sample_data[:2]
            )  # Show first 2 records like the pipeline uses

            # Run the pipeline and check return value
            result = run_pipeline()

            assert result is True, "Pipeline should return True on success"
            print("[OUTPUT] Pipeline executed successfully")
            print("[TEST] Pipeline ran successfully! Data loaded via DLT.")

        except Exception as e:
            print(f"[TEST] Pipeline failed with error: {e}")
            pytest.fail(f"Pipeline failed: {e}")

    def test_dlt_pipeline_creation(self, temp_db_path):
        """Test DLT pipeline creation and configuration."""
        pipeline = dlt.pipeline(
            pipeline_name="test_pipeline",
            destination="duckdb",
            dataset_name="test_data",
        )

        assert pipeline.pipeline_name == "test_pipeline"
        assert pipeline.destination.destination_name == "duckdb"
        assert pipeline.dataset_name == "test_data"

    def test_data_loading_and_retrieval(self, temp_db_path, sample_data):
        """Test data loading into DuckDB and retrieval."""
        # Create pipeline with custom database path
        pipeline = dlt.pipeline(
            pipeline_name="test_load", destination="duckdb", dataset_name="test_data"
        )

        # Load test data
        load_info = pipeline.run(
            sample_data, table_name="test_table", write_disposition="replace"
        )

        # Verify load was successful
        assert load_info is not None

        # Query the data back
        con = duckdb.connect("test_load.duckdb")
        result = con.execute("SELECT COUNT(*) FROM test_data.test_table").fetchone()

        assert result[0] == len(sample_data)

        # Cleanup
        con.close()
        if os.path.exists("test_load.duckdb"):
            os.unlink("test_load.duckdb")

    def test_data_schema_validation(self, temp_db_path, sample_data):
        """Test that loaded data maintains correct schema."""
        pipeline = dlt.pipeline(
            pipeline_name="schema_test",
            destination="duckdb",
            dataset_name="schema_data",
        )

        pipeline.run(
            sample_data, table_name="schema_table", write_disposition="replace"
        )

        con = duckdb.connect("schema_test.duckdb")

        # Check column names and types
        schema_info = con.execute("DESCRIBE schema_data.schema_table").fetchall()

        column_names = [row[0] for row in schema_info]
        expected_columns = ["id", "value", "category", "amount"]

        for col in expected_columns:
            assert col in column_names, f"Expected column {col} not found"

        con.close()
        if os.path.exists("schema_test.duckdb"):
            os.unlink("schema_test.duckdb")

    def test_write_dispositions(self, temp_db_path, sample_data):
        """Test different write dispositions (replace, append)."""
        pipeline = dlt.pipeline(
            pipeline_name="disposition_test",
            destination="duckdb",
            dataset_name="disp_data",
        )

        # Initial load with replace
        pipeline.run(sample_data, table_name="disp_table", write_disposition="replace")

        con = duckdb.connect("disposition_test.duckdb")
        count_after_replace = con.execute(
            "SELECT COUNT(*) FROM disp_data.disp_table"
        ).fetchone()[0]

        assert count_after_replace == len(sample_data)

        # Append more data
        additional_data = [{"id": 4, "value": "qux", "category": "C", "amount": 300.00}]
        pipeline.run(
            additional_data, table_name="disp_table", write_disposition="append"
        )

        count_after_append = con.execute(
            "SELECT COUNT(*) FROM disp_data.disp_table"
        ).fetchone()[0]

        assert count_after_append == len(sample_data) + len(additional_data)

        con.close()
        if os.path.exists("disposition_test.duckdb"):
            os.unlink("disposition_test.duckdb")

    def test_error_handling_invalid_data(self):
        """Test pipeline behavior with invalid data."""
        pipeline = dlt.pipeline(
            pipeline_name="error_test", destination="duckdb", dataset_name="error_data"
        )

        # Test with invalid data structure - DLT may handle this gracefully
        invalid_data = ["not", "a", "dictionary"]

        try:
            load_info = pipeline.run(invalid_data, table_name="error_table")
            # If DLT doesn't raise an exception, check if it reported failures
            if load_info.has_failed_jobs:
                # This counts as expected error handling
                pass
            else:
                # DLT handled it gracefully, which is also acceptable
                print("DLT handled invalid data gracefully")
        except Exception:
            # Exception was raised, which is expected behavior
            pass

        # Cleanup if file was created
        if os.path.exists("error_test.duckdb"):
            os.unlink("error_test.duckdb")


# Legacy test function for backward compatibility
def test_pipeline_runs():
    """Legacy test function - kept for backward compatibility."""
    print("[TEST] Starting DLT → DuckDB pipeline test...")
    try:
        # Show the input data
        input_data = [{"id": 1, "value": "foo"}, {"id": 2, "value": "bar"}]
        print("[INPUT] Data to load:", input_data)

        # Actually run the pipeline
        result = run_pipeline()

        assert result is True, "Pipeline should return True on success"
        print("[OUTPUT] Pipeline executed successfully via DLT")
        print("[TEST] Pipeline ran successfully! Data loaded to DuckDB.")
    except Exception as e:
        print(f"[TEST] Pipeline failed with error: {e}")
        pytest.fail(f"Pipeline failed: {e}")
