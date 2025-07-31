import dlt
import duckdb


def run_pipeline():
    # Example: Load sample data with DLT and write to DuckDB
    data = [{"id": 1, "value": "foo"}, {"id": 2, "value": "bar"}]
    pipeline = dlt.pipeline(
        pipeline_name="sample", destination="duckdb", dataset_name="sample_data"
    )
    load_info = pipeline.run(data, table_name="my_table", write_disposition="replace")
    print("DLT Load Info:", load_info)

    # Since DLT structure may be complex, let's just verify the load was successful
    # and return success based on DLT's report
    if load_info and not load_info.has_failed_jobs:
        print("DLT pipeline executed successfully")
        print(f"Loaded {len(data)} records to my_table")
        return True
    else:
        print("DLT pipeline failed")
        return False


if __name__ == "__main__":
    run_pipeline()
