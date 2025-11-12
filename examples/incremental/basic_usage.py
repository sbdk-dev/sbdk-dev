"""
Basic Incremental Processing Example

Demonstrates how to use SBDK's incremental processing engine
for timestamp-based incremental loading.
"""

from datetime import datetime
from sbdk.pipeline import (
    IncrementalProcessor,
    IncrementalConfig,
    IncrementalStrategy,
    IncrementalMode,
)


def main():
    """Run basic incremental processing example."""

    # Initialize processor
    processor = IncrementalProcessor("example_pipeline")

    # Configure incremental strategy
    config = IncrementalConfig(
        strategy=IncrementalStrategy.TIMESTAMP,
        watermark_column="updated_at",
        mode=IncrementalMode.APPEND
    )

    # Define data processing function
    def process_data():
        """Extract and load data incrementally."""

        # Get last watermark
        last_value = processor.get_last_watermark(config)

        print(f"Last watermark: {last_value or 'None (initial run)'}")

        # Simulate data extraction
        # In real use, this would query your database:
        # SELECT * FROM source WHERE updated_at > '{last_value}'
        if last_value:
            print(f"Extracting data since {last_value}...")
            # Incremental load
            new_records = [
                {"id": 4, "name": "New User", "updated_at": "2025-01-15T12:00:00"},
                {"id": 5, "name": "Another User", "updated_at": "2025-01-15T13:00:00"},
            ]
        else:
            print("Initial load - extracting all data...")
            # Full load
            new_records = [
                {"id": 1, "name": "User 1", "updated_at": "2025-01-15T10:00:00"},
                {"id": 2, "name": "User 2", "updated_at": "2025-01-15T10:30:00"},
                {"id": 3, "name": "User 3", "updated_at": "2025-01-15T11:00:00"},
            ]

        # Process records
        print(f"Processing {len(new_records)} records...")

        # Calculate new watermark (max timestamp)
        if new_records:
            max_timestamp = max(r["updated_at"] for r in new_records)
        else:
            max_timestamp = last_value

        return {
            "records_processed": len(new_records),
            "max_timestamp": max_timestamp
        }

    # Execute with automatic state tracking
    result = processor.process(
        process_data,
        config,
        extract_watermark=lambda r: r["max_timestamp"]
    )

    # Display results
    print("\n" + "="*50)
    print("RESULTS:")
    print(f"  Success: {result['success']}")
    print(f"  Records processed: {result['records_processed']}")
    print(f"  New watermark: {result['new_watermark']}")
    print(f"  Run ID: {result['run_id']}")
    print("="*50)

    # View state
    state = processor.get_state()
    if state and state.incremental:
        print(f"\nCurrent state:")
        print(f"  Strategy: {state.incremental.strategy}")
        print(f"  Last value: {state.incremental.last_value}")
        print(f"  Total records processed: {state.incremental.records_processed}")


if __name__ == "__main__":
    print("SBDK Incremental Processing - Basic Example")
    print("="*50)
    print("\nRun 1: Initial load")
    main()

    print("\n\n" + "="*50)
    print("Run 2: Incremental load")
    main()

    print("\n\nExample complete!")
    print("Check .sbdk/state/example_pipeline/ for state files")
