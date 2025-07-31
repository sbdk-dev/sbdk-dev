import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from pipeline import run_pipeline


def test_pipeline_runs():
    print("[TEST] Starting DLT → DuckDB pipeline test...")
    try:
        # Show the input data
        input_data = [{"id": 1, "value": "foo"}, {"id": 2, "value": "bar"}]
        print("[INPUT] Data to load:", input_data)
        print("[INPUT] Query: SELECT * FROM sample_data.my_table")
        # Actually run the pipeline
        run_pipeline()
        # Show expected output (the table rows)
        print("[OUTPUT] If successful, you should see the loaded rows printed above.")
        print("[TEST] Pipeline ran successfully! Data loaded and queried from DuckDB.")
    except Exception as e:
        print(f"[TEST] Pipeline failed with error: {e}")
        assert False, f"Pipeline failed: {e}"
