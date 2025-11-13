"""
Tests for SBDK Pipeline State Management

Test coverage:
- IncrementalState model validation
- PipelineState model validation and methods
- StateManager file operations
- State persistence and retrieval
- History tracking
- Configuration change detection
- Error handling
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from sbdk.exceptions import FileSystemError, ValidationError
from sbdk.pipeline.state import (
    IncrementalState,
    PipelineState,
    StateManager,
)


class TestIncrementalState:
    """Test IncrementalState model."""

    def test_create_incremental_state_minimal(self):
        """Test creating incremental state with minimal fields."""
        state = IncrementalState(strategy="timestamp")

        assert state.strategy == "timestamp"
        assert state.last_value is None
        assert state.records_processed == 0
        assert isinstance(state.last_updated, datetime)
        assert state.metadata == {}

    def test_create_incremental_state_full(self):
        """Test creating incremental state with all fields."""
        timestamp = datetime.utcnow()
        state = IncrementalState(
            strategy="timestamp",
            last_value="2025-01-01T00:00:00",
            last_updated=timestamp,
            records_processed=1000,
            metadata={"source": "api", "version": "v1"}
        )

        assert state.strategy == "timestamp"
        assert state.last_value == "2025-01-01T00:00:00"
        assert state.last_updated == timestamp
        assert state.records_processed == 1000
        assert state.metadata == {"source": "api", "version": "v1"}

    def test_incremental_state_invalid_strategy(self):
        """Test validation fails for invalid strategy."""
        with pytest.raises(ValueError, match="strategy"):
            IncrementalState(strategy="invalid_strategy")

    def test_incremental_state_empty_last_value(self):
        """Test validation fails for empty string last_value."""
        with pytest.raises(ValueError, match="cannot be empty"):
            IncrementalState(strategy="timestamp", last_value="   ")

    def test_incremental_state_negative_records(self):
        """Test validation fails for negative records_processed."""
        with pytest.raises(ValueError):
            IncrementalState(strategy="timestamp", records_processed=-1)

    def test_incremental_state_json_serialization(self):
        """Test JSON serialization works correctly."""
        state = IncrementalState(
            strategy="hash",
            last_value="abc123",
            records_processed=500
        )

        json_str = state.model_dump_json()
        data = json.loads(json_str)

        assert data["strategy"] == "hash"
        assert data["last_value"] == "abc123"
        assert data["records_processed"] == 500
        assert "last_updated" in data


class TestPipelineState:
    """Test PipelineState model."""

    def test_create_pipeline_state_minimal(self):
        """Test creating pipeline state with minimal fields."""
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4())
        )

        assert state.pipeline_name == "test_pipeline"
        assert state.run_id
        assert state.status == "running"
        assert state.completed_at is None
        assert state.incremental is None
        assert state.metrics == {}
        assert state.errors == []

    def test_create_pipeline_state_full(self):
        """Test creating pipeline state with all fields."""
        run_id = str(uuid.uuid4())
        incremental = IncrementalState(strategy="timestamp")

        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=run_id,
            status="completed",
            incremental=incremental,
            metrics={"rows": 1000},
            errors=[],
            config_hash="abc123"
        )

        assert state.pipeline_name == "test_pipeline"
        assert state.run_id == run_id
        assert state.status == "completed"
        assert state.incremental == incremental
        assert state.metrics == {"rows": 1000}
        assert state.config_hash == "abc123"

    def test_pipeline_state_invalid_name(self):
        """Test validation fails for invalid pipeline name."""
        with pytest.raises(ValueError):
            PipelineState(pipeline_name="", run_id=str(uuid.uuid4()))

        with pytest.raises(ValueError):
            PipelineState(pipeline_name="invalid name!", run_id=str(uuid.uuid4()))

    def test_pipeline_state_invalid_status(self):
        """Test validation fails for invalid status."""
        with pytest.raises(ValueError):
            PipelineState(
                pipeline_name="test",
                run_id=str(uuid.uuid4()),
                status="invalid_status"
            )

    def test_mark_completed(self):
        """Test marking pipeline as completed."""
        state = PipelineState(
            pipeline_name="test",
            run_id=str(uuid.uuid4())
        )

        assert state.status == "running"
        assert state.completed_at is None

        state.mark_completed({"rows": 100})

        assert state.status == "completed"
        assert state.completed_at is not None
        assert state.metrics["rows"] == 100

    def test_mark_failed(self):
        """Test marking pipeline as failed."""
        state = PipelineState(
            pipeline_name="test",
            run_id=str(uuid.uuid4())
        )

        state.mark_failed("Connection timeout")

        assert state.status == "failed"
        assert state.completed_at is not None
        assert "Connection timeout" in state.errors

    def test_get_duration_seconds(self):
        """Test calculating execution duration."""
        state = PipelineState(
            pipeline_name="test",
            run_id=str(uuid.uuid4())
        )

        # Not completed yet
        assert state.get_duration_seconds() is None

        # Mark completed
        state.started_at = datetime.utcnow() - timedelta(seconds=10)
        state.mark_completed()

        duration = state.get_duration_seconds()
        assert duration is not None
        assert duration >= 9  # At least 9 seconds (accounting for timing variations)


class TestStateManager:
    """Test StateManager functionality."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create temporary state directory."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return state_dir

    @pytest.fixture
    def state_manager(self, temp_state_dir):
        """Create StateManager with temp directory."""
        return StateManager(temp_state_dir)

    def test_init_creates_state_dir(self, tmp_path):
        """Test StateManager creates state directory."""
        state_dir = tmp_path / "new_state"
        assert not state_dir.exists()

        manager = StateManager(state_dir)

        assert state_dir.exists()
        assert manager.state_dir == state_dir

    def test_save_and_load_state(self, state_manager):
        """Test saving and loading pipeline state."""
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            status="running"
        )

        # Save state
        state_manager.save_state(state)

        # Load state
        loaded = state_manager.load_state("test_pipeline")

        assert loaded is not None
        assert loaded.pipeline_name == state.pipeline_name
        assert loaded.run_id == state.run_id
        assert loaded.status == state.status

    def test_load_nonexistent_state(self, state_manager):
        """Test loading state for nonexistent pipeline."""
        loaded = state_manager.load_state("nonexistent")
        assert loaded is None

    def test_save_state_creates_history(self, state_manager):
        """Test completed state is saved to history."""
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4())
        )
        state.mark_completed()

        state_manager.save_state(state)

        # Check history file exists
        history_dir = state_manager._get_history_dir("test_pipeline")
        history_files = list(history_dir.glob("*.json"))

        assert len(history_files) == 1

    def test_get_incremental_state(self, state_manager):
        """Test getting incremental state from pipeline state."""
        incremental = IncrementalState(
            strategy="timestamp",
            last_value="2025-01-01T00:00:00"
        )
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4()),
            incremental=incremental
        )

        state_manager.save_state(state)

        loaded_incr = state_manager.get_incremental_state("test_pipeline")

        assert loaded_incr is not None
        assert loaded_incr.strategy == "timestamp"
        assert loaded_incr.last_value == "2025-01-01T00:00:00"

    def test_get_incremental_state_none(self, state_manager):
        """Test getting incremental state when none exists."""
        loaded = state_manager.get_incremental_state("nonexistent")
        assert loaded is None

    def test_update_incremental_state(self, state_manager):
        """Test updating incremental state."""
        # Create initial state
        state = PipelineState(
            pipeline_name="test_pipeline",
            run_id=str(uuid.uuid4())
        )
        state_manager.save_state(state)

        # Update incremental state
        state_manager.update_incremental_state(
            "test_pipeline",
            strategy="timestamp",
            last_value="2025-01-02T00:00:00",
            records_processed=100,
            metadata={"source": "api"}
        )

        # Load and verify
        loaded = state_manager.load_state("test_pipeline")
        assert loaded.incremental is not None
        assert loaded.incremental.strategy == "timestamp"
        assert loaded.incremental.last_value == "2025-01-02T00:00:00"
        assert loaded.incremental.records_processed == 100
        assert loaded.incremental.metadata["source"] == "api"

    def test_update_incremental_state_accumulates_records(self, state_manager):
        """Test updating incremental state accumulates record counts."""
        state = PipelineState(
            pipeline_name="test",
            run_id=str(uuid.uuid4()),
            incremental=IncrementalState(
                strategy="timestamp",
                last_value="2025-01-01T00:00:00",
                records_processed=100
            )
        )
        state_manager.save_state(state)

        # Update with more records
        state_manager.update_incremental_state(
            "test",
            strategy="timestamp",
            last_value="2025-01-02T00:00:00",
            records_processed=50
        )

        loaded = state_manager.load_state("test")
        assert loaded.incremental.records_processed == 150  # 100 + 50

    def test_update_incremental_state_no_pipeline(self, state_manager):
        """Test updating incremental state for nonexistent pipeline fails."""
        with pytest.raises(ValidationError, match="No state found"):
            state_manager.update_incremental_state(
                "nonexistent",
                strategy="timestamp",
                last_value="2025-01-01T00:00:00",
                records_processed=100
            )

    def test_list_history(self, state_manager):
        """Test listing pipeline run history."""
        # Create multiple runs
        for i in range(5):
            state = PipelineState(
                pipeline_name="test",
                run_id=str(uuid.uuid4())
            )
            state.mark_completed()
            state_manager.save_state(state)

        history = state_manager.list_history("test")

        assert len(history) == 5
        # Should be sorted by most recent first
        assert all(isinstance(s, PipelineState) for s in history)

    def test_list_history_with_limit(self, state_manager):
        """Test listing history with limit."""
        # Create 5 runs
        for i in range(5):
            state = PipelineState(
                pipeline_name="test",
                run_id=str(uuid.uuid4())
            )
            state.mark_completed()
            state_manager.save_state(state)

        history = state_manager.list_history("test", limit=3)

        assert len(history) == 3

    def test_list_history_empty(self, state_manager):
        """Test listing history for pipeline with no history."""
        history = state_manager.list_history("nonexistent")
        assert history == []

    def test_clear_state(self, state_manager):
        """Test clearing pipeline state."""
        state = PipelineState(
            pipeline_name="test",
            run_id=str(uuid.uuid4())
        )
        state_manager.save_state(state)

        # Verify state exists
        assert state_manager.load_state("test") is not None

        # Clear state
        state_manager.clear_state("test")

        # Verify state cleared
        assert state_manager.load_state("test") is None

    def test_clear_state_with_history(self, state_manager):
        """Test clearing state including history."""
        # Create state with history
        for i in range(3):
            state = PipelineState(
                pipeline_name="test",
                run_id=str(uuid.uuid4())
            )
            state.mark_completed()
            state_manager.save_state(state)

        # Clear including history
        state_manager.clear_state("test", include_history=True)

        # Verify both current and history cleared
        assert state_manager.load_state("test") is None
        assert state_manager.list_history("test") == []

    def test_compute_config_hash(self, state_manager):
        """Test computing configuration hash."""
        config1 = {"pipeline": "test", "batch_size": 100}
        config2 = {"batch_size": 100, "pipeline": "test"}  # Different order
        config3 = {"pipeline": "test", "batch_size": 200}  # Different value

        hash1 = state_manager.compute_config_hash(config1)
        hash2 = state_manager.compute_config_hash(config2)
        hash3 = state_manager.compute_config_hash(config3)

        # Same config different order = same hash
        assert hash1 == hash2

        # Different config = different hash
        assert hash1 != hash3

    def test_has_config_changed_no_previous(self, state_manager):
        """Test config change detection with no previous state."""
        config = {"pipeline": "test"}
        changed = state_manager.has_config_changed("test", config)

        assert changed is True

    def test_has_config_changed_same_config(self, state_manager):
        """Test config change detection with same config."""
        config = {"pipeline": "test", "batch_size": 100}

        # Save state with config hash
        state = PipelineState(
            pipeline_name="test",
            run_id=str(uuid.uuid4()),
            config_hash=state_manager.compute_config_hash(config)
        )
        state_manager.save_state(state)

        # Check if changed
        changed = state_manager.has_config_changed("test", config)

        assert changed is False

    def test_has_config_changed_different_config(self, state_manager):
        """Test config change detection with different config."""
        config1 = {"pipeline": "test", "batch_size": 100}
        config2 = {"pipeline": "test", "batch_size": 200}

        # Save state with config1 hash
        state = PipelineState(
            pipeline_name="test",
            run_id=str(uuid.uuid4()),
            config_hash=state_manager.compute_config_hash(config1)
        )
        state_manager.save_state(state)

        # Check if config2 changed
        changed = state_manager.has_config_changed("test", config2)

        assert changed is True

    def test_corrupted_state_file_raises_error(self, state_manager, temp_state_dir):
        """Test loading corrupted state file raises ValidationError."""
        # Create corrupted state file
        pipeline_dir = temp_state_dir / "test_pipeline"
        pipeline_dir.mkdir()
        state_file = pipeline_dir / "current.json"
        state_file.write_text("{ invalid json }")

        with pytest.raises(ValidationError, match="Corrupted state file"):
            state_manager.load_state("test_pipeline")

    def test_state_manager_default_dir(self, tmp_path, monkeypatch):
        """Test StateManager uses default .sbdk/state directory."""
        monkeypatch.chdir(tmp_path)

        manager = StateManager()

        expected_dir = Path(".sbdk") / "state"
        assert manager.state_dir == expected_dir
        assert expected_dir.exists()
        # Verify it's in the temp directory
        assert (tmp_path / ".sbdk" / "state").exists()


class TestStateIntegration:
    """Integration tests for state management."""

    @pytest.fixture
    def state_manager(self, tmp_path):
        """Create StateManager with temp directory."""
        return StateManager(tmp_path / "state")

    def test_full_pipeline_lifecycle(self, state_manager):
        """Test complete pipeline lifecycle with state tracking."""
        pipeline_name = "integration_test"

        # 1. Start first run
        run1_id = str(uuid.uuid4())
        state1 = PipelineState(
            pipeline_name=pipeline_name,
            run_id=run1_id,
            incremental=IncrementalState(
                strategy="timestamp",
                last_value=None,
                records_processed=0
            )
        )
        state_manager.save_state(state1)

        # 2. Complete first run
        state1.incremental.last_value = "2025-01-01T00:00:00"
        state1.incremental.records_processed = 1000
        state1.mark_completed({"rows": 1000})
        state_manager.save_state(state1)

        # 3. Start second run (incremental)
        run2_id = str(uuid.uuid4())
        loaded = state_manager.load_state(pipeline_name)
        assert loaded.incremental.last_value == "2025-01-01T00:00:00"

        state2 = PipelineState(
            pipeline_name=pipeline_name,
            run_id=run2_id,
            incremental=IncrementalState(
                strategy="timestamp",
                last_value=loaded.incremental.last_value,
                records_processed=0
            )
        )
        state_manager.save_state(state2)

        # 4. Complete second run
        state2.incremental.last_value = "2025-01-02T00:00:00"
        state2.incremental.records_processed = 50
        state2.mark_completed({"rows": 50})
        state_manager.save_state(state2)

        # 5. Verify history
        history = state_manager.list_history(pipeline_name)
        assert len(history) == 2

        # 6. Verify current state
        current = state_manager.load_state(pipeline_name)
        assert current.run_id == run2_id
        assert current.incremental.last_value == "2025-01-02T00:00:00"
