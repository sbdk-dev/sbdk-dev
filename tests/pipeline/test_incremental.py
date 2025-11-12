"""
Tests for SBDK Incremental Processing Engine

Test coverage:
- IncrementalConfig validation
- IncrementalProcessor initialization
- Watermark tracking (timestamp, hash, watermark)
- SQL filter building
- Hash computation and change detection
- Pipeline run lifecycle
- Error handling and recovery
- Integration with StateManager
- Utility functions
"""

import uuid
from datetime import datetime
from pathlib import Path

import pytest

from sbdk.exceptions import PipelineError, ValidationError
from sbdk.pipeline.incremental import (
    IncrementalConfig,
    IncrementalMode,
    IncrementalProcessor,
    IncrementalStrategy,
    create_hash_processor,
    create_timestamp_processor,
)
from sbdk.pipeline.state import IncrementalState, PipelineState


class TestIncrementalStrategy:
    """Test IncrementalStrategy enum."""

    def test_strategy_values(self):
        """Test strategy enum values."""
        assert IncrementalStrategy.TIMESTAMP.value == "timestamp"
        assert IncrementalStrategy.HASH.value == "hash"
        assert IncrementalStrategy.WATERMARK.value == "watermark"
        assert IncrementalStrategy.FULL.value == "full"


class TestIncrementalMode:
    """Test IncrementalMode enum."""

    def test_mode_values(self):
        """Test mode enum values."""
        assert IncrementalMode.APPEND.value == "append"
        assert IncrementalMode.MERGE.value == "merge"
        assert IncrementalMode.DELETE_INSERT.value == "delete_insert"


class TestIncrementalConfig:
    """Test IncrementalConfig model."""

    def test_create_config_defaults(self):
        """Test creating config with defaults."""
        config = IncrementalConfig()

        assert config.strategy == IncrementalStrategy.TIMESTAMP
        assert config.mode == IncrementalMode.APPEND
        assert config.unique_key == "id"
        assert config.force_full_refresh is False

    def test_create_config_timestamp_strategy(self):
        """Test creating config for timestamp strategy."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        assert config.strategy == IncrementalStrategy.TIMESTAMP
        assert config.watermark_column == "updated_at"

    def test_create_config_hash_strategy(self):
        """Test creating config for hash strategy."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key=["user_id", "product_id"],
            check_columns=["price", "quantity"]
        )

        assert config.strategy == IncrementalStrategy.HASH
        assert config.unique_key == ["user_id", "product_id"]
        assert config.check_columns == ["price", "quantity"]

    def test_config_requires_watermark_for_timestamp(self):
        """Test timestamp strategy requires watermark_column."""
        with pytest.raises(ValueError, match="watermark_column required"):
            IncrementalConfig(
                strategy=IncrementalStrategy.TIMESTAMP,
                watermark_column=None
            )

    def test_config_requires_watermark_for_watermark_strategy(self):
        """Test watermark strategy requires watermark_column."""
        with pytest.raises(ValueError, match="watermark_column required"):
            IncrementalConfig(
                strategy=IncrementalStrategy.WATERMARK,
                watermark_column=""
            )

    def test_config_allows_none_watermark_for_hash(self):
        """Test hash strategy doesn't require watermark_column."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            watermark_column=None
        )

        assert config.watermark_column is None

    def test_config_allows_none_watermark_for_full(self):
        """Test full refresh doesn't require watermark_column."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.FULL,
            watermark_column=None
        )

        assert config.watermark_column is None


class TestIncrementalProcessor:
    """Test IncrementalProcessor functionality."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create temporary state directory."""
        return tmp_path / "state"

    @pytest.fixture
    def processor(self, temp_state_dir):
        """Create IncrementalProcessor with temp state dir."""
        return IncrementalProcessor("test_pipeline", temp_state_dir)

    def test_init_processor(self, temp_state_dir):
        """Test initializing processor."""
        processor = IncrementalProcessor("test_pipeline", temp_state_dir)

        assert processor.pipeline_name == "test_pipeline"
        assert processor.state_manager.state_dir == temp_state_dir
        assert processor.run_id

    def test_init_invalid_pipeline_name(self, temp_state_dir):
        """Test initialization fails with invalid pipeline name."""
        with pytest.raises(ValidationError, match="Invalid pipeline name"):
            IncrementalProcessor("invalid@name!", temp_state_dir)

        with pytest.raises(ValidationError):
            IncrementalProcessor("", temp_state_dir)

    def test_get_last_watermark_no_state(self, processor):
        """Test getting watermark with no previous state."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        watermark = processor.get_last_watermark(config)

        assert watermark is None

    def test_get_last_watermark_with_state(self, processor):
        """Test getting watermark with existing state."""
        # Create state
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            incremental=IncrementalState(
                strategy="timestamp",
                last_value="2025-01-01T00:00:00"
            )
        )
        processor.state_manager.save_state(state)

        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        watermark = processor.get_last_watermark(config)

        assert watermark == "2025-01-01T00:00:00"

    def test_get_last_watermark_force_refresh(self, processor):
        """Test force refresh ignores previous watermark."""
        # Create state
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            incremental=IncrementalState(
                strategy="timestamp",
                last_value="2025-01-01T00:00:00"
            )
        )
        processor.state_manager.save_state(state)

        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at",
            force_full_refresh=True
        )

        watermark = processor.get_last_watermark(config)

        assert watermark is None

    def test_get_last_watermark_strategy_mismatch(self, processor, capsys):
        """Test watermark with strategy change triggers warning."""
        # Create state with timestamp strategy
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            incremental=IncrementalState(
                strategy="timestamp",
                last_value="2025-01-01T00:00:00"
            )
        )
        processor.state_manager.save_state(state)

        # Try to use hash strategy
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key="id"
        )

        watermark = processor.get_last_watermark(config)

        # Should return None and print warning
        assert watermark is None

    def test_build_incremental_filter_timestamp(self, processor):
        """Test building filter for timestamp strategy."""
        # Create state
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            incremental=IncrementalState(
                strategy="timestamp",
                last_value="2025-01-01T00:00:00"
            )
        )
        processor.state_manager.save_state(state)

        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        filter_sql = processor.build_incremental_filter(config)

        assert filter_sql == "updated_at > '2025-01-01T00:00:00'"

    def test_build_incremental_filter_watermark(self, processor):
        """Test building filter for watermark strategy."""
        # Create state
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            incremental=IncrementalState(
                strategy="watermark",
                last_value="12345"
            )
        )
        processor.state_manager.save_state(state)

        config = IncrementalConfig(
            strategy=IncrementalStrategy.WATERMARK,
            watermark_column="sequence_id"
        )

        filter_sql = processor.build_incremental_filter(config)

        assert filter_sql == "sequence_id > '12345'"

    def test_build_incremental_filter_no_state(self, processor):
        """Test building filter with no previous state."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        filter_sql = processor.build_incremental_filter(config)

        assert filter_sql is None

    def test_build_incremental_filter_full_refresh(self, processor):
        """Test building filter for full refresh."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.FULL
        )

        filter_sql = processor.build_incremental_filter(config)

        assert filter_sql is None

    def test_build_incremental_filter_hash_returns_none(self, processor):
        """Test hash strategy doesn't use SQL filter."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key="id"
        )

        filter_sql = processor.build_incremental_filter(config)

        assert filter_sql is None

    def test_build_incremental_filter_missing_watermark_column(self, processor):
        """Test building filter fails without watermark column."""
        # Create state
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            incremental=IncrementalState(
                strategy="timestamp",
                last_value="2025-01-01T00:00:00"
            )
        )
        processor.state_manager.save_state(state)

        # Valid timestamp config (has watermark)
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="created_at"
        )

        # Build filter should work with valid config
        filter_sql = processor.build_incremental_filter(config)
        assert filter_sql == "created_at > '2025-01-01T00:00:00'"

    def test_compute_row_hash_all_columns(self, processor):
        """Test computing hash with all columns."""
        row = {"id": 1, "name": "Alice", "price": 100}

        hash1 = processor.compute_row_hash(row)
        hash2 = processor.compute_row_hash(row)

        # Same row = same hash
        assert hash1 == hash2

        # Different row = different hash
        row2 = {"id": 1, "name": "Alice", "price": 200}
        hash3 = processor.compute_row_hash(row2)
        assert hash1 != hash3

    def test_compute_row_hash_specific_columns(self, processor):
        """Test computing hash with specific columns."""
        row = {"id": 1, "name": "Alice", "price": 100, "updated_at": "2025-01-01"}

        # Hash only price and name
        hash1 = processor.compute_row_hash(row, check_columns=["name", "price"])

        # Change updated_at but not checked columns
        row2 = {"id": 1, "name": "Alice", "price": 100, "updated_at": "2025-01-02"}
        hash2 = processor.compute_row_hash(row2, check_columns=["name", "price"])

        # Hashes should be same (updated_at not checked)
        assert hash1 == hash2

        # Change checked column
        row3 = {"id": 1, "name": "Alice", "price": 200, "updated_at": "2025-01-01"}
        hash3 = processor.compute_row_hash(row3, check_columns=["name", "price"])

        # Hash should differ
        assert hash1 != hash3

    def test_filter_changed_rows_first_run(self, processor):
        """Test filtering changed rows on first run."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key="id"
        )

        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]

        changed = processor.filter_changed_rows(rows, config, previous_hashes=None)

        # First run, all rows are new
        assert len(changed) == 2

    def test_filter_changed_rows_no_changes(self, processor):
        """Test filtering rows with no changes."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key="id"
        )

        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]

        # Compute hashes
        previous_hashes = {
            "1": processor.compute_row_hash(rows[0]),
            "2": processor.compute_row_hash(rows[1])
        }

        changed = processor.filter_changed_rows(rows, config, previous_hashes)

        # No changes
        assert len(changed) == 0

    def test_filter_changed_rows_with_changes(self, processor):
        """Test filtering rows with changes."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key="id"
        )

        old_rows = [
            {"id": 1, "name": "Alice", "price": 100},
            {"id": 2, "name": "Bob", "price": 200}
        ]

        # Compute previous hashes
        previous_hashes = {
            "1": processor.compute_row_hash(old_rows[0]),
            "2": processor.compute_row_hash(old_rows[1])
        }

        # New rows with one changed
        new_rows = [
            {"id": 1, "name": "Alice", "price": 100},  # Unchanged
            {"id": 2, "name": "Bob", "price": 250},    # Changed
            {"id": 3, "name": "Charlie", "price": 150} # New
        ]

        changed = processor.filter_changed_rows(new_rows, config, previous_hashes)

        # Should have 2 changed rows (id 2 and 3)
        assert len(changed) == 2
        assert any(r["id"] == 2 for r in changed)
        assert any(r["id"] == 3 for r in changed)

    def test_filter_changed_rows_composite_key(self, processor):
        """Test filtering with composite unique key."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key=["user_id", "product_id"]
        )

        old_rows = [
            {"user_id": 1, "product_id": 10, "quantity": 5}
        ]

        previous_hashes = {
            "1:10": processor.compute_row_hash(old_rows[0])
        }

        new_rows = [
            {"user_id": 1, "product_id": 10, "quantity": 5},  # Unchanged
            {"user_id": 1, "product_id": 20, "quantity": 3},  # New
        ]

        changed = processor.filter_changed_rows(new_rows, config, previous_hashes)

        assert len(changed) == 1
        assert changed[0]["product_id"] == 20

    def test_filter_changed_rows_non_hash_strategy(self, processor):
        """Test filtering returns all rows for non-hash strategies."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        rows = [{"id": 1}, {"id": 2}]
        previous_hashes = {"1": "hash1"}

        changed = processor.filter_changed_rows(rows, config, previous_hashes)

        # Non-hash strategy returns all rows
        assert len(changed) == 2

    def test_start_run(self, processor):
        """Test starting a pipeline run."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        state = processor.start_run(config)

        assert state.pipeline_name == "test_pipeline"
        assert state.run_id == processor.run_id
        assert state.status == "running"
        assert state.incremental is not None
        assert state.incremental.strategy == "timestamp"

    def test_start_run_with_config_hash(self, processor):
        """Test starting run tracks config hash."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )
        pipeline_config = {"batch_size": 100, "source": "api"}

        state = processor.start_run(config, pipeline_config)

        assert state.config_hash is not None

    def test_start_run_full_refresh(self, processor):
        """Test starting run with full refresh."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.FULL
        )

        state = processor.start_run(config)

        # Full refresh doesn't create incremental state
        assert state.incremental is None

    def test_complete_run(self, processor):
        """Test completing a pipeline run."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        # Start run
        processor.start_run(config)

        # Complete run
        processor.complete_run(
            new_watermark="2025-01-02T00:00:00",
            records_processed=100,
            metrics={"rows_inserted": 100}
        )

        # Verify state
        state = processor.state_manager.load_state("test_pipeline")
        assert state.status == "completed"
        assert state.incremental.last_value == "2025-01-02T00:00:00"
        assert state.incremental.records_processed == 100
        assert state.metrics["records_processed"] == 100
        assert state.metrics["rows_inserted"] == 100

    def test_complete_run_no_start(self, processor):
        """Test completing run without start fails."""
        with pytest.raises(ValidationError, match="No active run found"):
            processor.complete_run("2025-01-01T00:00:00", 100)

    def test_fail_run(self, processor):
        """Test failing a pipeline run."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        # Start run
        processor.start_run(config)

        # Fail run
        processor.fail_run("Connection timeout")

        # Verify state
        state = processor.state_manager.load_state("test_pipeline")
        assert state.status == "failed"
        assert "Connection timeout" in state.errors

    def test_fail_run_without_start(self, processor):
        """Test failing run without start creates minimal state."""
        processor.fail_run("Error")

        state = processor.state_manager.load_state("test_pipeline")
        assert state.status == "failed"

    def test_process_success(self, processor):
        """Test successful processing with process() method."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        def process_data():
            return {
                "records_processed": 100,
                "max_timestamp": "2025-01-02T00:00:00"
            }

        result = processor.process(
            process_data,
            config,
            extract_watermark=lambda r: r["max_timestamp"]
        )

        assert result["success"] is True
        assert result["records_processed"] == 100
        assert result["new_watermark"] == "2025-01-02T00:00:00"

        # Verify state updated
        state = processor.state_manager.load_state("test_pipeline")
        assert state.status == "completed"

    def test_process_with_list_result(self, processor):
        """Test processing with list result."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key="id"
        )

        def process_data():
            return [{"id": 1}, {"id": 2}, {"id": 3}]

        result = processor.process(process_data, config)

        assert result["success"] is True
        assert result["records_processed"] == 3

    def test_process_failure(self, processor):
        """Test processing failure handling."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        def process_data():
            raise ValueError("Processing error")

        with pytest.raises(PipelineError, match="Incremental processing failed"):
            processor.process(process_data, config)

        # Verify state marked as failed
        state = processor.state_manager.load_state("test_pipeline")
        assert state.status == "failed"

    def test_reset_state(self, processor):
        """Test resetting pipeline state."""
        # Create state
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )
        processor.start_run(config)

        # Verify state exists
        assert processor.get_state() is not None

        # Reset state
        processor.reset_state()

        # Verify state cleared
        assert processor.get_state() is None

    def test_get_state(self, processor):
        """Test getting current state."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        # No state initially
        assert processor.get_state() is None

        # Create state
        processor.start_run(config)

        # State should exist
        state = processor.get_state()
        assert state is not None
        assert state.pipeline_name == "test_pipeline"

    def test_get_history(self, processor):
        """Test getting pipeline history."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        # Create multiple runs
        for i in range(3):
            # Need to create new processor for each run (new run_id)
            proc = IncrementalProcessor("test_pipeline", processor.state_manager.state_dir)
            proc.start_run(config)
            proc.complete_run(f"2025-01-0{i+1}T00:00:00", 100)

        history = processor.get_history()

        assert len(history) == 3

    def test_get_history_with_limit(self, processor):
        """Test getting history with limit."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="updated_at"
        )

        # Create 5 runs
        for i in range(5):
            proc = IncrementalProcessor("test_pipeline", processor.state_manager.state_dir)
            proc.start_run(config)
            proc.complete_run(f"2025-01-0{i+1}T00:00:00", 100)

        history = processor.get_history(limit=2)

        assert len(history) == 2


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_timestamp_processor(self, tmp_path):
        """Test creating timestamp-based processor."""
        processor = create_timestamp_processor(
            "test_pipeline",
            "updated_at",
            tmp_path / "state"
        )

        assert processor.pipeline_name == "test_pipeline"
        assert processor.state_manager.state_dir == tmp_path / "state"

    def test_create_hash_processor(self, tmp_path):
        """Test creating hash-based processor."""
        processor = create_hash_processor(
            "test_pipeline",
            "id",
            check_columns=["name", "price"],
            state_dir=tmp_path / "state"
        )

        assert processor.pipeline_name == "test_pipeline"


class TestIncrementalIntegration:
    """Integration tests for incremental processing."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create processor with temp state."""
        return IncrementalProcessor("integration_test", tmp_path / "state")

    def test_full_incremental_workflow(self, processor):
        """Test complete incremental workflow over multiple runs."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="created_at"
        )

        # Run 1: Initial full load
        def run1():
            return {
                "records_processed": 1000,
                "max_timestamp": "2025-01-01T12:00:00"
            }

        result1 = processor.process(
            run1,
            config,
            extract_watermark=lambda r: r["max_timestamp"]
        )

        assert result1["success"] is True
        assert result1["records_processed"] == 1000

        # Run 2: Incremental load
        processor2 = IncrementalProcessor(
            "integration_test",
            processor.state_manager.state_dir
        )

        # Should get last watermark
        last_value = processor2.get_last_watermark(config)
        assert last_value == "2025-01-01T12:00:00"

        def run2():
            # Simulate incremental load
            return {
                "records_processed": 50,
                "max_timestamp": "2025-01-02T12:00:00"
            }

        result2 = processor2.process(
            run2,
            config,
            extract_watermark=lambda r: r["max_timestamp"]
        )

        assert result2["success"] is True
        assert result2["records_processed"] == 50

        # Run 3: Force full refresh
        processor3 = IncrementalProcessor(
            "integration_test",
            processor.state_manager.state_dir
        )

        config_refresh = IncrementalConfig(
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="created_at",
            force_full_refresh=True
        )

        last_value_refresh = processor3.get_last_watermark(config_refresh)
        assert last_value_refresh is None  # Should be None for full refresh

    def test_hash_based_incremental_workflow(self, processor):
        """Test hash-based change detection workflow."""
        config = IncrementalConfig(
            strategy=IncrementalStrategy.HASH,
            unique_key="id",
            check_columns=["name", "price"]
        )

        # Initial data
        initial_data = [
            {"id": 1, "name": "Product A", "price": 100},
            {"id": 2, "name": "Product B", "price": 200}
        ]

        # Compute initial hashes
        hashes = {
            str(row["id"]): processor.compute_row_hash(row, config.check_columns)
            for row in initial_data
        }

        # Updated data (one changed, one new)
        updated_data = [
            {"id": 1, "name": "Product A", "price": 100},  # Unchanged
            {"id": 2, "name": "Product B", "price": 250},  # Price changed
            {"id": 3, "name": "Product C", "price": 150}   # New
        ]

        changed = processor.filter_changed_rows(updated_data, config, hashes)

        # Should detect 2 changes
        assert len(changed) == 2
        assert any(r["id"] == 2 for r in changed)  # Changed
        assert any(r["id"] == 3 for r in changed)  # New
