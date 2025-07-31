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
    # Query with DuckDB
    con = duckdb.connect("sample.duckdb")
    # If you want a pandas DataFrame (requires pandas and numpy):
    df = con.execute("SELECT * FROM sample_data.my_table").df()
    print(df)


if __name__ == "__main__":
    run_pipeline()
