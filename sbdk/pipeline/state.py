"""
SBDK Pipeline State Management

Manages pipeline execution state, tracking incremental processing metadata,
watermarks, checksums, and execution history.

State is persisted in .sbdk/state/ directory as JSON files, enabling:
- Incremental processing (only new/changed data)
- Watermark tracking (timestamp, hash, sequence)
- Run history and metadata
- State rollback and recovery
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from sbdk.exceptions import FileSystemError, ValidationError


class IncrementalState(BaseModel):
    """
    Incremental processing state for a pipeline.

    Tracks watermarks and metadata for incremental loading strategies.

    Attributes:
        strategy: Incremental strategy used (timestamp, hash, watermark)
        last_value: Last processed value (timestamp, hash, or sequence number)
        last_updated: When state was last updated
        records_processed: Total records processed in this state
        metadata: Additional strategy-specific metadata
    """

    strategy: str = Field(
        ...,
        description="Incremental strategy (timestamp, hash, watermark, full)",
        pattern="^(timestamp|hash|watermark|full)$"
    )
    last_value: Optional[str] = Field(
        default=None,
        description="Last processed value (timestamp, hash, or sequence)"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When state was last updated"
    )
    records_processed: int = Field(
        default=0,
        ge=0,
        description="Total records processed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific metadata"
    )

    @field_validator("last_value")
    @classmethod
    def validate_last_value(cls, v: Optional[str]) -> Optional[str]:
        """Validate last_value is not empty string."""
        if v is not None and v.strip() == "":
            raise ValueError("last_value cannot be empty string")
        return v

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineState(BaseModel):
    """
    Complete state for a pipeline execution.

    Stores execution metadata, incremental state, and run history.

    Attributes:
        pipeline_name: Unique pipeline identifier
        run_id: Unique run identifier (UUID)
        started_at: Pipeline start timestamp
        completed_at: Pipeline completion timestamp (None if running)
        status: Execution status (running, completed, failed)
        incremental: Incremental processing state
        metrics: Execution metrics (rows processed, duration, etc.)
        errors: List of errors encountered
        config_hash: Hash of pipeline configuration for change detection
    """

    pipeline_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Pipeline identifier"
    )
    run_id: str = Field(
        ...,
        description="Unique run identifier"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Pipeline start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Pipeline completion timestamp"
    )
    status: str = Field(
        default="running",
        pattern="^(running|completed|failed|cancelled)$",
        description="Execution status"
    )
    incremental: Optional[IncrementalState] = Field(
        default=None,
        description="Incremental processing state"
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Errors encountered during execution"
    )
    config_hash: Optional[str] = Field(
        default=None,
        description="Configuration hash for change detection"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def mark_completed(self, metrics: Optional[dict[str, Any]] = None) -> None:
        """
        Mark pipeline as completed.

        Args:
            metrics: Optional execution metrics to merge
        """
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if metrics:
            self.metrics.update(metrics)

    def mark_failed(self, error: str) -> None:
        """
        Mark pipeline as failed.

        Args:
            error: Error message
        """
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.errors.append(error)

    def get_duration_seconds(self) -> Optional[float]:
        """
        Get pipeline execution duration in seconds.

        Returns:
            Duration in seconds, or None if not completed
        """
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()


class StateManager:
    """
    Manages pipeline state persistence and retrieval.

    Handles reading/writing state files, maintaining state history,
    and providing APIs for state queries.

    State files are stored in .sbdk/state/ with structure:
    - .sbdk/state/{pipeline_name}/current.json - Current state
    - .sbdk/state/{pipeline_name}/history/{run_id}.json - Run history

    Attributes:
        state_dir: Root directory for state storage
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize state manager.

        Args:
            state_dir: Custom state directory (default: .sbdk/state)
        """
        self.state_dir = state_dir or Path(".sbdk/state")
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_pipeline_dir(self, pipeline_name: str) -> Path:
        """
        Get state directory for a pipeline.

        Args:
            pipeline_name: Pipeline identifier

        Returns:
            Path to pipeline state directory
        """
        pipeline_dir = self.state_dir / pipeline_name
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        return pipeline_dir

    def _get_history_dir(self, pipeline_name: str) -> Path:
        """
        Get history directory for a pipeline.

        Args:
            pipeline_name: Pipeline identifier

        Returns:
            Path to pipeline history directory
        """
        history_dir = self._get_pipeline_dir(pipeline_name) / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir

    def save_state(self, state: PipelineState) -> None:
        """
        Save pipeline state to disk.

        Saves both current state and historical record.

        Args:
            state: Pipeline state to save

        Raises:
            FileSystemError: If save operation fails
        """
        pipeline_dir = self._get_pipeline_dir(state.pipeline_name)
        current_path = pipeline_dir / "current.json"

        try:
            # Save current state
            with open(current_path, "w") as f:
                f.write(state.model_dump_json(indent=2))

            # Save to history if completed or failed
            if state.status in ["completed", "failed"]:
                history_dir = self._get_history_dir(state.pipeline_name)
                history_path = history_dir / f"{state.run_id}.json"
                with open(history_path, "w") as f:
                    f.write(state.model_dump_json(indent=2))

        except (IOError, OSError) as e:
            raise FileSystemError(
                f"Failed to save pipeline state: {e}",
                suggestion="Check file permissions and disk space"
            ) from e

    def load_state(self, pipeline_name: str) -> Optional[PipelineState]:
        """
        Load current state for a pipeline.

        Args:
            pipeline_name: Pipeline identifier

        Returns:
            Pipeline state if exists, None otherwise

        Raises:
            ValidationError: If state file is corrupted
        """
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        current_path = pipeline_dir / "current.json"

        if not current_path.exists():
            return None

        try:
            with open(current_path) as f:
                data = json.load(f)
            return PipelineState(**data)

        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Corrupted state file for pipeline '{pipeline_name}': {e}",
                suggestion=f"Delete corrupted state: {current_path}"
            ) from e

    def get_incremental_state(
        self, pipeline_name: str
    ) -> Optional[IncrementalState]:
        """
        Get incremental state for a pipeline.

        Args:
            pipeline_name: Pipeline identifier

        Returns:
            Incremental state if exists, None otherwise
        """
        state = self.load_state(pipeline_name)
        return state.incremental if state else None

    def update_incremental_state(
        self,
        pipeline_name: str,
        strategy: str,
        last_value: str,
        records_processed: int,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Update incremental state for a pipeline.

        Args:
            pipeline_name: Pipeline identifier
            strategy: Incremental strategy
            last_value: New last processed value
            records_processed: Number of records processed
            metadata: Optional metadata to merge

        Raises:
            ValidationError: If pipeline state doesn't exist
        """
        state = self.load_state(pipeline_name)
        if state is None:
            raise ValidationError(
                f"No state found for pipeline '{pipeline_name}'",
                suggestion="Run pipeline at least once before updating incremental state"
            )

        # Update incremental state
        if state.incremental is None:
            state.incremental = IncrementalState(
                strategy=strategy,
                last_value=last_value,
                records_processed=records_processed,
                metadata=metadata or {}
            )
        else:
            state.incremental.last_value = last_value
            state.incremental.last_updated = datetime.utcnow()
            state.incremental.records_processed += records_processed
            if metadata:
                state.incremental.metadata.update(metadata)

        self.save_state(state)

    def list_history(
        self, pipeline_name: str, limit: Optional[int] = None
    ) -> list[PipelineState]:
        """
        List historical runs for a pipeline.

        Args:
            pipeline_name: Pipeline identifier
            limit: Maximum number of runs to return (most recent first)

        Returns:
            List of historical pipeline states
        """
        history_dir = self._get_history_dir(pipeline_name)

        if not history_dir.exists():
            return []

        history_files = sorted(
            history_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if limit:
            history_files = history_files[:limit]

        states = []
        for file_path in history_files:
            try:
                with open(file_path) as f:
                    data = json.load(f)
                states.append(PipelineState(**data))
            except (json.JSONDecodeError, ValueError):
                # Skip corrupted files
                continue

        return states

    def clear_state(self, pipeline_name: str, include_history: bool = False) -> None:
        """
        Clear state for a pipeline.

        Args:
            pipeline_name: Pipeline identifier
            include_history: Also clear history (default: False)

        Raises:
            FileSystemError: If deletion fails
        """
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        current_path = pipeline_dir / "current.json"

        try:
            if current_path.exists():
                current_path.unlink()

            if include_history:
                history_dir = self._get_history_dir(pipeline_name)
                if history_dir.exists():
                    for file_path in history_dir.glob("*.json"):
                        file_path.unlink()

        except OSError as e:
            raise FileSystemError(
                f"Failed to clear state for pipeline '{pipeline_name}': {e}",
                suggestion="Check file permissions"
            ) from e

    def compute_config_hash(self, config: dict[str, Any]) -> str:
        """
        Compute hash of pipeline configuration.

        Args:
            config: Pipeline configuration dictionary

        Returns:
            SHA256 hash of configuration
        """
        config_json = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()

    def has_config_changed(
        self, pipeline_name: str, config: dict[str, Any]
    ) -> bool:
        """
        Check if pipeline configuration has changed.

        Args:
            pipeline_name: Pipeline identifier
            config: Current pipeline configuration

        Returns:
            True if configuration changed or no previous state exists
        """
        state = self.load_state(pipeline_name)
        if state is None or state.config_hash is None:
            return True

        current_hash = self.compute_config_hash(config)
        return current_hash != state.config_hash
