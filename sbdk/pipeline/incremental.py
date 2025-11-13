"""
SBDK Incremental Processing Engine

Implements incremental data processing strategies to enable efficient,
fast iteration cycles by only processing new or changed data.

Supports multiple strategies:
- Timestamp-based: Process records newer than last watermark
- Hash-based: Process records with changed content
- Watermark-based: Generic watermark tracking (sequence, version, etc.)
- Full: Full refresh (no incremental processing)

Integration points:
- DLT pipelines: Automatic state management
- dbt models: Incremental model support
- Custom pipelines: Flexible API for any use case
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Union

from pydantic import BaseModel, Field, field_validator
from rich.console import Console

from sbdk.exceptions import PipelineError, ValidationError
from sbdk.pipeline.state import (
    IncrementalState,
    PipelineState,
    StateManager,
)

console = Console()


class IncrementalStrategy(str, Enum):
    """
    Incremental processing strategies.

    - TIMESTAMP: Use timestamp column for incremental loading
    - HASH: Use content hash for change detection
    - WATERMARK: Use custom watermark column (sequence, version, etc.)
    - FULL: Full refresh, no incremental processing
    """
    TIMESTAMP = "timestamp"
    HASH = "hash"
    WATERMARK = "watermark"
    FULL = "full"


class IncrementalMode(str, Enum):
    """
    Incremental processing modes.

    - APPEND: Only append new records
    - MERGE: Merge changes (upsert)
    - DELETE_INSERT: Delete and insert changed records
    """
    APPEND = "append"
    MERGE = "merge"
    DELETE_INSERT = "delete_insert"


class IncrementalConfig(BaseModel):
    """
    Configuration for incremental processing.

    Attributes:
        strategy: Incremental strategy to use
        mode: Processing mode (append, merge, delete+insert)
        watermark_column: Column name for watermark (timestamp/sequence)
        unique_key: Column(s) for identifying unique records
        check_columns: Columns to check for changes (hash strategy)
        state_dir: Custom state directory
        force_full_refresh: Force full refresh ignoring state
    """

    strategy: IncrementalStrategy = Field(
        default=IncrementalStrategy.TIMESTAMP,
        description="Incremental strategy"
    )
    mode: IncrementalMode = Field(
        default=IncrementalMode.APPEND,
        description="Processing mode"
    )
    watermark_column: Optional[str] = Field(
        default=None,
        description="Column for watermark tracking"
    )
    unique_key: Union[str, list[str]] = Field(
        default="id",
        description="Unique key column(s)"
    )
    check_columns: Optional[list[str]] = Field(
        default=None,
        description="Columns to check for changes (hash strategy)"
    )
    state_dir: Optional[Path] = Field(
        default=None,
        description="Custom state directory"
    )
    force_full_refresh: bool = Field(
        default=False,
        description="Force full refresh"
    )

    @field_validator("watermark_column")
    @classmethod
    def validate_watermark_column(cls, v: Optional[str], info) -> Optional[str]:
        """Validate watermark column is provided for timestamp/watermark strategies."""
        strategy = info.data.get("strategy")
        if strategy in [IncrementalStrategy.TIMESTAMP, IncrementalStrategy.WATERMARK]:
            if v is None or v.strip() == "":
                raise ValueError(
                    f"watermark_column required for {strategy.value} strategy"
                )
        return v

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class IncrementalProcessor:
    """
    Incremental processing engine for data pipelines.

    Manages incremental state, computes incremental queries,
    and tracks processing progress.

    Example:
        >>> processor = IncrementalProcessor("users_pipeline")
        >>> config = IncrementalConfig(
        ...     strategy=IncrementalStrategy.TIMESTAMP,
        ...     watermark_column="updated_at"
        ... )
        >>>
        >>> # Get last watermark
        >>> last_value = processor.get_last_watermark(config)
        >>>
        >>> # Process data
        >>> new_data = extract_data(since=last_value)
        >>> processor.process(new_data, config)
    """

    def __init__(
        self,
        pipeline_name: str,
        state_dir: Optional[Path] = None
    ):
        """
        Initialize incremental processor.

        Args:
            pipeline_name: Unique pipeline identifier
            state_dir: Custom state directory (default: .sbdk/state)

        Raises:
            ValidationError: If pipeline_name is invalid
        """
        if not pipeline_name or not pipeline_name.replace("-", "").replace("_", "").isalnum():
            raise ValidationError(
                f"Invalid pipeline name: {pipeline_name}",
                suggestion="Use alphanumeric characters, hyphens, and underscores"
            )

        self.pipeline_name = pipeline_name
        self.state_manager = StateManager(state_dir)
        self.run_id = str(uuid.uuid4())

    def get_last_watermark(
        self, config: IncrementalConfig
    ) -> Optional[str]:
        """
        Get last processed watermark value.

        Args:
            config: Incremental configuration

        Returns:
            Last watermark value, or None for initial run
        """
        if config.force_full_refresh:
            return None

        incremental_state = self.state_manager.get_incremental_state(
            self.pipeline_name
        )

        if incremental_state is None:
            return None

        # Verify strategy matches
        if incremental_state.strategy != config.strategy.value:
            console.print(
                f"[yellow]Warning: Strategy changed from {incremental_state.strategy} "
                f"to {config.strategy.value}, performing full refresh[/yellow]"
            )
            return None

        return incremental_state.last_value

    def build_incremental_filter(
        self, config: IncrementalConfig, dialect: str = "duckdb"
    ) -> Optional[str]:
        """
        Build SQL filter for incremental processing.

        Args:
            config: Incremental configuration
            dialect: SQL dialect (duckdb, postgres, bigquery)

        Returns:
            SQL WHERE clause, or None for full refresh

        Example:
            >>> processor = IncrementalProcessor("users")
            >>> config = IncrementalConfig(
            ...     strategy=IncrementalStrategy.TIMESTAMP,
            ...     watermark_column="updated_at"
            ... )
            >>> filter_sql = processor.build_incremental_filter(config)
            >>> # Returns: "updated_at > '2025-01-01T00:00:00'"
        """
        last_value = self.get_last_watermark(config)

        if last_value is None:
            return None

        if config.strategy == IncrementalStrategy.FULL:
            return None

        watermark_col = config.watermark_column
        if not watermark_col:
            raise ValidationError(
                "watermark_column required for incremental filter",
                suggestion="Specify watermark_column in IncrementalConfig"
            )

        # Build filter based on strategy
        if config.strategy == IncrementalStrategy.TIMESTAMP:
            # Timestamp comparison
            return f"{watermark_col} > '{last_value}'"

        elif config.strategy == IncrementalStrategy.WATERMARK:
            # Generic watermark comparison
            return f"{watermark_col} > '{last_value}'"

        else:
            # Hash strategy doesn't use SQL filter
            return None

    def compute_row_hash(
        self,
        row: dict[str, Any],
        check_columns: Optional[list[str]] = None
    ) -> str:
        """
        Compute hash for a data row.

        Args:
            row: Data row as dictionary
            check_columns: Columns to include in hash (None = all columns)

        Returns:
            SHA256 hash of row data
        """
        if check_columns:
            row_data = {k: v for k, v in row.items() if k in check_columns}
        else:
            row_data = row

        # Sort keys for consistent hashing
        row_str = str(sorted(row_data.items()))
        return hashlib.sha256(row_str.encode()).hexdigest()

    def filter_changed_rows(
        self,
        rows: list[dict[str, Any]],
        config: IncrementalConfig,
        previous_hashes: Optional[dict[str, str]] = None
    ) -> list[dict[str, Any]]:
        """
        Filter rows to only changed records (hash strategy).

        Args:
            rows: List of data rows
            config: Incremental configuration
            previous_hashes: Previous row hashes (key -> hash)

        Returns:
            List of changed rows
        """
        if config.strategy != IncrementalStrategy.HASH:
            return rows

        if previous_hashes is None:
            # First run, all rows are new
            return rows

        changed_rows = []
        unique_key = config.unique_key
        if isinstance(unique_key, str):
            unique_key = [unique_key]

        for row in rows:
            # Get unique key value
            key_values = [str(row.get(col)) for col in unique_key]
            row_key = ":".join(key_values)

            # Compute current hash
            current_hash = self.compute_row_hash(row, config.check_columns)

            # Check if changed
            if row_key not in previous_hashes or previous_hashes[row_key] != current_hash:
                changed_rows.append(row)

        return changed_rows

    def start_run(
        self, config: IncrementalConfig, pipeline_config: Optional[dict[str, Any]] = None
    ) -> PipelineState:
        """
        Start a new pipeline run.

        Args:
            config: Incremental configuration
            pipeline_config: Pipeline configuration for hash tracking

        Returns:
            Pipeline state for this run
        """
        state = PipelineState(
            pipeline_name=self.pipeline_name,
            run_id=self.run_id,
            status="running",
        )

        # Add config hash if provided
        if pipeline_config:
            state.config_hash = self.state_manager.compute_config_hash(pipeline_config)

        # Initialize incremental state if needed
        if config.strategy != IncrementalStrategy.FULL:
            last_value = self.get_last_watermark(config)
            state.incremental = IncrementalState(
                strategy=config.strategy.value,
                last_value=last_value,
                records_processed=0
            )

        self.state_manager.save_state(state)
        return state

    def complete_run(
        self,
        new_watermark: Optional[str],
        records_processed: int,
        metrics: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Complete pipeline run and update state.

        Args:
            new_watermark: New watermark value (timestamp, hash, sequence)
            records_processed: Number of records processed
            metrics: Optional execution metrics

        Raises:
            ValidationError: If run state doesn't exist
        """
        state = self.state_manager.load_state(self.pipeline_name)
        if state is None or state.run_id != self.run_id:
            raise ValidationError(
                f"No active run found for pipeline '{self.pipeline_name}'",
                suggestion="Call start_run() before complete_run()"
            )

        # Update incremental state
        if state.incremental and new_watermark:
            state.incremental.last_value = new_watermark
            state.incremental.last_updated = datetime.utcnow()
            state.incremental.records_processed += records_processed

        # Mark completed
        run_metrics = {
            "records_processed": records_processed,
            "duration_seconds": state.get_duration_seconds() or 0,
        }
        if metrics:
            run_metrics.update(metrics)

        state.mark_completed(run_metrics)
        self.state_manager.save_state(state)

        # Log completion
        console.print(
            f"[green]✅ Pipeline '{self.pipeline_name}' completed: "
            f"{records_processed} records processed[/green]"
        )

    def fail_run(self, error: str) -> None:
        """
        Mark pipeline run as failed.

        Args:
            error: Error message
        """
        state = self.state_manager.load_state(self.pipeline_name)
        if state is None or state.run_id != self.run_id:
            # Create minimal failed state
            state = PipelineState(
                pipeline_name=self.pipeline_name,
                run_id=self.run_id,
                status="failed"
            )

        state.mark_failed(error)
        self.state_manager.save_state(state)

        console.print(
            f"[red]❌ Pipeline '{self.pipeline_name}' failed: {error}[/red]"
        )

    def process(
        self,
        data_fn: Callable[[], Any],
        config: IncrementalConfig,
        extract_watermark: Optional[Callable[[Any], str]] = None,
        pipeline_config: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Process data with incremental strategy.

        High-level API that handles the complete incremental flow:
        1. Start run
        2. Execute data function
        3. Update state
        4. Return results

        Args:
            data_fn: Function that processes data and returns results
            config: Incremental configuration
            extract_watermark: Function to extract watermark from results
            pipeline_config: Pipeline configuration for change tracking

        Returns:
            Processing results with metadata

        Raises:
            PipelineError: If processing fails

        Example:
            >>> processor = IncrementalProcessor("users")
            >>> config = IncrementalConfig(
            ...     strategy=IncrementalStrategy.TIMESTAMP,
            ...     watermark_column="updated_at"
            ... )
            >>>
            >>> def process_users():
            ...     last_value = processor.get_last_watermark(config)
            ...     data = fetch_users(since=last_value)
            ...     load_users(data)
            ...     return {"rows": data, "max_timestamp": max(r["updated_at"] for r in data)}
            >>>
            >>> result = processor.process(
            ...     process_users,
            ...     config,
            ...     extract_watermark=lambda r: r["max_timestamp"]
            ... )
        """
        try:
            # Start run
            state = self.start_run(config, pipeline_config)

            # Execute data processing
            result = data_fn()

            # Extract watermark
            new_watermark = None
            records_processed = 0

            if extract_watermark and result:
                new_watermark = extract_watermark(result)

            if isinstance(result, dict):
                records_processed = result.get("records_processed", 0)
            elif isinstance(result, list):
                records_processed = len(result)

            # Complete run
            self.complete_run(
                new_watermark,
                records_processed,
                metrics=result if isinstance(result, dict) else None
            )

            return {
                "success": True,
                "pipeline_name": self.pipeline_name,
                "run_id": self.run_id,
                "records_processed": records_processed,
                "new_watermark": new_watermark,
                "result": result
            }

        except Exception as e:
            # Mark run as failed
            self.fail_run(str(e))

            raise PipelineError(
                f"Incremental processing failed for '{self.pipeline_name}': {e}",
                suggestion="Check pipeline logs and fix errors"
            ) from e

    def reset_state(self, include_history: bool = False) -> None:
        """
        Reset pipeline state for fresh start.

        Args:
            include_history: Also clear history (default: False)
        """
        self.state_manager.clear_state(self.pipeline_name, include_history)
        console.print(
            f"[yellow]State reset for pipeline '{self.pipeline_name}'[/yellow]"
        )

    def get_state(self) -> Optional[PipelineState]:
        """
        Get current pipeline state.

        Returns:
            Current pipeline state, or None if not exists
        """
        return self.state_manager.load_state(self.pipeline_name)

    def get_history(self, limit: int = 10) -> list[PipelineState]:
        """
        Get pipeline run history.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of historical pipeline states
        """
        return self.state_manager.list_history(self.pipeline_name, limit)


# Utility functions for common incremental patterns

def create_timestamp_processor(
    pipeline_name: str,
    watermark_column: str,
    state_dir: Optional[Path] = None
) -> IncrementalProcessor:
    """
    Create processor for timestamp-based incremental loading.

    Args:
        pipeline_name: Pipeline identifier
        watermark_column: Timestamp column name
        state_dir: Custom state directory

    Returns:
        Configured incremental processor

    Example:
        >>> processor = create_timestamp_processor("users", "updated_at")
        >>> config = IncrementalConfig(
        ...     strategy=IncrementalStrategy.TIMESTAMP,
        ...     watermark_column="updated_at"
        ... )
        >>> last_ts = processor.get_last_watermark(config)
    """
    return IncrementalProcessor(pipeline_name, state_dir)


def create_hash_processor(
    pipeline_name: str,
    unique_key: Union[str, list[str]],
    check_columns: Optional[list[str]] = None,
    state_dir: Optional[Path] = None
) -> IncrementalProcessor:
    """
    Create processor for hash-based change detection.

    Args:
        pipeline_name: Pipeline identifier
        unique_key: Unique key column(s)
        check_columns: Columns to check for changes
        state_dir: Custom state directory

    Returns:
        Configured incremental processor

    Example:
        >>> processor = create_hash_processor("products", "product_id")
        >>> config = IncrementalConfig(
        ...     strategy=IncrementalStrategy.HASH,
        ...     unique_key="product_id",
        ...     check_columns=["price", "stock", "description"]
        ... )
    """
    return IncrementalProcessor(pipeline_name, state_dir)
