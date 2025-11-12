"""
File System Watcher for SBDK Hot-Reload Development Mode

Monitors file system changes and triggers pipeline reloads with smart change
detection, debouncing, and rich console output for real-time feedback.

This module implements the watchdog pattern for efficient file monitoring
with support for:
- Pattern-based file filtering (*.py, *.sql, *.yaml)
- Debouncing to prevent reload spam (500ms default)
- Recursive directory watching
- Clear status reporting with Rich console
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from rich.console import Console
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from sbdk.exceptions import SBDKError


class WatcherError(SBDKError):
    """Raised when file watcher operations fail."""

    exit_code = 2


@dataclass
class WatchConfig:
    """
    Configuration for file watcher behavior.

    Attributes:
        watch_patterns: File extensions to watch (e.g., ['.py', '.sql', '.yaml'])
        debounce_seconds: Minimum time between reload triggers
        recursive: Whether to watch subdirectories
        exclude_dirs: Directories to exclude from watching (e.g., ['.git', '__pycache__'])
        quiet: Suppress non-essential output
        verbose: Show detailed change information
    """

    watch_patterns: list[str] = field(default_factory=lambda: [".py", ".sql", ".yaml", ".yml"])
    debounce_seconds: float = 0.5
    recursive: bool = True
    exclude_dirs: list[str] = field(default_factory=lambda: [".git", "__pycache__", ".venv", "node_modules"])
    quiet: bool = False
    verbose: bool = False

    def matches_pattern(self, path: str) -> bool:
        """
        Check if file path matches watch patterns.

        Args:
            path: File path to check

        Returns:
            True if file matches any watch pattern
        """
        return any(path.endswith(pattern) for pattern in self.watch_patterns)

    def should_ignore_dir(self, path: str) -> bool:
        """
        Check if directory should be ignored.

        Args:
            path: Directory path to check

        Returns:
            True if directory should be ignored
        """
        return any(excluded in Path(path).parts for excluded in self.exclude_dirs)


class ChangeAggregator:
    """
    Aggregates rapid file changes to detect coherent change sets.

    Tracks recent changes and groups them to provide meaningful feedback
    about what triggered reloads.
    """

    def __init__(self, max_history: int = 10) -> None:
        """
        Initialize change aggregator.

        Args:
            max_history: Maximum number of recent changes to track
        """
        self.changes: list[tuple[float, str]] = []
        self.max_history = max_history

    def add_change(self, path: str) -> None:
        """
        Record a file change.

        Args:
            path: Path of changed file
        """
        self.changes.append((time.time(), path))
        # Keep only recent changes
        if len(self.changes) > self.max_history:
            self.changes.pop(0)

    def get_recent_changes(self, seconds: float = 1.0) -> list[str]:
        """
        Get changes from the last N seconds.

        Args:
            seconds: Time window to look back

        Returns:
            List of file paths that changed in the time window
        """
        cutoff = time.time() - seconds
        return [path for ts, path in self.changes if ts >= cutoff]

    def get_summary(self) -> dict[str, int]:
        """
        Get summary of changes by type.

        Returns:
            Dictionary with file extension counts
        """
        summary: dict[str, int] = {}
        for _, path in self.changes:
            ext = Path(path).suffix or "no_extension"
            summary[ext] = summary.get(ext, 0) + 1
        return summary


class DebounceHandler(FileSystemEventHandler):
    """
    File system event handler with debouncing and smart change detection.

    Prevents rapid repeated reloads and provides clear feedback about
    what triggered the reload.
    """

    def __init__(
        self,
        callback: Callable[[], None],
        config: Optional[WatchConfig] = None,
        console: Optional[Console] = None
    ) -> None:
        """
        Initialize debounce handler.

        Args:
            callback: Function to call when changes detected
            config: Watch configuration
            console: Rich console for output (creates new if None)
        """
        self.callback = callback
        self.config = config or WatchConfig()
        self.console = console or Console()
        self.last_triggered = 0.0
        self.aggregator = ChangeAggregator()

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification events.

        Args:
            event: FileSystemEvent from watchdog
        """
        # Ignore directories
        if event.is_directory:
            return

        # Check if file matches patterns and not excluded
        if not self.config.matches_pattern(event.src_path):
            return

        if self.config.should_ignore_dir(event.src_path):
            return

        # Record the change
        self.aggregator.add_change(event.src_path)

        # Apply debouncing
        current_time = time.time()
        if current_time - self.last_triggered < self.config.debounce_seconds:
            if self.config.verbose and not self.config.quiet:
                self.console.print(
                    f"[dim]⏱️  Debounced: {event.src_path}[/dim]"
                )
            return

        self.last_triggered = current_time

        # Report change and trigger callback
        if not self.config.quiet:
            self._report_change(event.src_path)

        try:
            self.callback()
        except Exception as e:
            self.console.print(f"[red]Error during reload: {e}[/red]")

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events (treat like modification).

        Args:
            event: FileSystemEvent from watchdog
        """
        if not event.is_directory:
            self.on_modified(event)

    def _report_change(self, changed_path: str) -> None:
        """
        Report file change to user.

        Args:
            changed_path: Path of changed file
        """
        try:
            relative_path = Path(changed_path).relative_to(Path.cwd())
        except ValueError:
            # If can't make relative to cwd, use the path as-is
            relative_path = Path(changed_path)

        self.console.print(f"[yellow]🔄 Changed: {relative_path}[/yellow]")

        if self.config.verbose:
            recent = self.aggregator.get_recent_changes(seconds=2.0)
            if len(recent) > 1:
                self.console.print(
                    f"[dim]  (+ {len(recent) - 1} other recent changes)[/dim]"
                )


class FileWatcher:
    """
    Main file watcher for SBDK hot-reload development mode.

    Orchestrates directory monitoring with configurable patterns, debouncing,
    and rich console feedback for optimal developer experience.

    Example:
        >>> watcher = FileWatcher(
        ...     paths=["."],
        ...     config=WatchConfig(debounce_seconds=0.5),
        ...     callback=reload_pipeline
        ... )
        >>> watcher.start()
        >>> # Modify files, see automatic reloads
        >>> watcher.stop()
    """

    def __init__(
        self,
        paths: list[str] | str = ".",
        config: Optional[WatchConfig] = None,
        callback: Optional[Callable[[], None]] = None,
        console: Optional[Console] = None
    ) -> None:
        """
        Initialize file watcher.

        Args:
            paths: Path(s) to watch (default: current directory)
            config: Watch configuration
            callback: Function to call when changes detected
            console: Rich console for output

        Raises:
            WatcherError: If path is invalid
        """
        # Normalize paths
        if isinstance(paths, str):
            paths = [paths]

        self.paths = [Path(p) for p in paths]
        self.config = config or WatchConfig()
        self.callback = callback or (lambda: None)
        self.console = console or Console()

        # Validate paths
        for path in self.paths:
            if not path.exists():
                raise WatcherError(
                    f"Watch path does not exist: {path}",
                    suggestion=f"Ensure directory exists before starting watch mode"
                )

        self.observer: Optional[Observer] = None
        self.is_running = False

    def start(self) -> None:
        """
        Start watching files for changes.

        Raises:
            WatcherError: If watcher fails to start
        """
        try:
            self.observer = Observer()
            handler = DebounceHandler(self.callback, self.config, self.console)

            for path in self.paths:
                self.observer.schedule(
                    handler,
                    str(path),
                    recursive=self.config.recursive
                )

            self.observer.start()
            self.is_running = True

            if not self.config.quiet:
                paths_str = ", ".join(str(p) for p in self.paths)
                self.console.print(
                    f"[cyan]👀 Watching {paths_str}[/cyan]",
                    style="dim"
                )
                if self.config.verbose:
                    self.console.print(
                        f"[dim]Patterns: {', '.join(self.config.watch_patterns)}[/dim]"
                    )

        except Exception as e:
            raise WatcherError(
                f"Failed to start file watcher: {e}",
                suggestion="Ensure watchdog is installed: pip install watchdog"
            ) from e

    def stop(self) -> None:
        """Stop watching files."""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False

            if not self.config.quiet:
                self.console.print(
                    "[yellow]👋 Stopped watching for changes[/yellow]",
                    style="dim"
                )

    def __enter__(self) -> "FileWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.stop()

    def __repr__(self) -> str:
        """String representation."""
        paths_str = ", ".join(str(p) for p in self.paths)
        return f"FileWatcher(paths=[{paths_str}], debounce={self.config.debounce_seconds}s)"
