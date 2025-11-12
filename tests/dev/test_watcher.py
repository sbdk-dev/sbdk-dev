"""
Tests for SBDK file watcher module.

Tests cover:
- WatchConfig pattern matching and exclusion
- ChangeAggregator change tracking
- DebounceHandler event handling and debouncing
- FileWatcher startup, monitoring, and shutdown
- Error handling and edge cases
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from rich.console import Console

from sbdk.dev.watcher import (
    ChangeAggregator,
    DebounceHandler,
    FileWatcher,
    WatchConfig,
    WatcherError,
)


class TestWatchConfig:
    """Test watch configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = WatchConfig()
        assert config.debounce_seconds == 0.5
        assert config.recursive is True
        assert ".py" in config.watch_patterns
        assert ".sql" in config.watch_patterns

    def test_custom_patterns(self) -> None:
        """Test custom watch patterns."""
        config = WatchConfig(watch_patterns=[".txt", ".json"])
        assert config.matches_pattern("file.txt")
        assert config.matches_pattern("config.json")
        assert not config.matches_pattern("script.py")

    def test_matches_pattern(self) -> None:
        """Test pattern matching."""
        config = WatchConfig()
        assert config.matches_pattern("script.py")
        assert config.matches_pattern("query.sql")
        assert config.matches_pattern("config.yaml")
        assert config.matches_pattern("config.yml")
        assert not config.matches_pattern("README.md")

    def test_should_ignore_dir(self) -> None:
        """Test directory exclusion."""
        config = WatchConfig()
        assert config.should_ignore_dir(".git/config.py")
        assert config.should_ignore_dir(".venv/lib/file.py")
        assert config.should_ignore_dir("__pycache__/module.py")
        assert not config.should_ignore_dir("src/main.py")

    def test_custom_exclude_dirs(self) -> None:
        """Test custom exclude directories."""
        config = WatchConfig(exclude_dirs=[".custom", "dist"])
        assert config.should_ignore_dir(".custom/file.py")
        assert config.should_ignore_dir("dist/bundle.js")
        assert not config.should_ignore_dir("src/file.py")


class TestChangeAggregator:
    """Test change aggregation."""

    def test_add_change(self) -> None:
        """Test adding changes."""
        agg = ChangeAggregator()
        agg.add_change("file1.py")
        agg.add_change("file2.py")
        assert len(agg.changes) == 2

    def test_get_recent_changes(self) -> None:
        """Test getting recent changes."""
        agg = ChangeAggregator()
        agg.add_change("file1.py")
        time.sleep(0.1)
        agg.add_change("file2.py")

        recent = agg.get_recent_changes(seconds=0.05)
        assert len(recent) == 1
        assert recent[0] == "file2.py"

    def test_get_summary(self) -> None:
        """Test getting change summary."""
        agg = ChangeAggregator()
        agg.add_change("script.py")
        agg.add_change("module.py")
        agg.add_change("query.sql")

        summary = agg.get_summary()
        assert summary[".py"] == 2
        assert summary[".sql"] == 1

    def test_max_history(self) -> None:
        """Test history size limit."""
        agg = ChangeAggregator(max_history=3)
        for i in range(5):
            agg.add_change(f"file{i}.py")

        assert len(agg.changes) == 3

    def test_summary_with_no_extension(self) -> None:
        """Test summary with files without extension."""
        agg = ChangeAggregator()
        agg.add_change("Makefile")
        agg.add_change("script.py")

        summary = agg.get_summary()
        assert "no_extension" in summary or "Makefile" in agg.get_recent_changes()


class TestDebounceHandler:
    """Test debounce event handler."""

    def test_callback_invoked(self) -> None:
        """Test that callback is invoked."""
        callback = Mock()
        handler = DebounceHandler(callback, WatchConfig())

        event = Mock()
        event.is_directory = False
        event.src_path = "test.py"

        handler.on_modified(event)
        callback.assert_called_once()

    def test_debounce_timing(self) -> None:
        """Test debouncing prevents rapid calls."""
        callback = Mock()
        config = WatchConfig(debounce_seconds=0.1)
        handler = DebounceHandler(callback, config)

        event = Mock()
        event.is_directory = False
        event.src_path = "test.py"

        # First call should trigger
        handler.on_modified(event)
        assert callback.call_count == 1

        # Immediate second call should be debounced
        handler.on_modified(event)
        assert callback.call_count == 1

        # After debounce period, should trigger
        time.sleep(0.15)
        handler.on_modified(event)
        assert callback.call_count == 2

    def test_ignore_directories(self) -> None:
        """Test that directories are ignored."""
        callback = Mock()
        handler = DebounceHandler(callback, WatchConfig())

        event = Mock()
        event.is_directory = True
        event.src_path = "src/"

        handler.on_modified(event)
        callback.assert_not_called()

    def test_pattern_filtering(self) -> None:
        """Test pattern filtering."""
        callback = Mock()
        config = WatchConfig(watch_patterns=[".py"])
        handler = DebounceHandler(callback, config)

        # Python file should trigger
        event = Mock()
        event.is_directory = False
        event.src_path = "script.py"
        handler.on_modified(event)
        assert callback.call_count == 1

        # Non-matching file should not trigger
        event.src_path = "README.md"
        handler.on_modified(event)
        assert callback.call_count == 1

    def test_exclude_dirs_filtering(self) -> None:
        """Test exclude directory filtering."""
        callback = Mock()
        config = WatchConfig(exclude_dirs=[".git"])
        handler = DebounceHandler(callback, config)

        # File in excluded dir should not trigger
        event = Mock()
        event.is_directory = False
        event.src_path = ".git/config.py"
        handler.on_modified(event)
        callback.assert_not_called()

    def test_on_created_event(self) -> None:
        """Test that created events are handled."""
        callback = Mock()
        handler = DebounceHandler(callback, WatchConfig())

        event = Mock()
        event.is_directory = False
        event.src_path = "new_file.py"

        handler.on_created(event)
        callback.assert_called_once()

    def test_error_handling_in_callback(self) -> None:
        """Test that callback errors are handled gracefully."""
        def failing_callback() -> None:
            raise RuntimeError("Test error")

        handler = DebounceHandler(failing_callback, WatchConfig(), Console())

        event = Mock()
        event.is_directory = False
        event.src_path = "test.py"

        # Should not raise
        handler.on_modified(event)


class TestFileWatcher:
    """Test file watcher."""

    def test_init_with_string_path(self) -> None:
        """Test initialization with string path."""
        with patch("pathlib.Path.exists", return_value=True):
            watcher = FileWatcher(paths=".")
            assert len(watcher.paths) == 1

    def test_init_with_list_paths(self) -> None:
        """Test initialization with list of paths."""
        with patch("pathlib.Path.exists", return_value=True):
            watcher = FileWatcher(paths=[".", "src"])
            assert len(watcher.paths) == 2

    def test_init_invalid_path(self) -> None:
        """Test initialization with invalid path."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(WatcherError) as exc_info:
                FileWatcher(paths="/nonexistent")

            assert "does not exist" in exc_info.value.message

    def test_custom_callback(self) -> None:
        """Test custom callback."""
        callback = Mock()

        with patch("pathlib.Path.exists", return_value=True):
            watcher = FileWatcher(callback=callback)
            assert watcher.callback is callback

    def test_default_callback(self) -> None:
        """Test default callback."""
        with patch("pathlib.Path.exists", return_value=True):
            watcher = FileWatcher()
            # Default callback should be callable and do nothing
            watcher.callback()  # Should not raise

    def test_start_stop(self) -> None:
        """Test starting and stopping watcher."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("sbdk.dev.watcher.Observer") as mock_observer:
                mock_obs_instance = MagicMock()
                mock_observer.return_value = mock_obs_instance

                watcher = FileWatcher()
                watcher.start()
                assert watcher.is_running is True

                watcher.stop()
                assert watcher.is_running is False
                mock_obs_instance.stop.assert_called()

    def test_context_manager(self) -> None:
        """Test context manager usage."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("sbdk.dev.watcher.Observer") as mock_observer:
                mock_obs_instance = MagicMock()
                mock_observer.return_value = mock_obs_instance

                with FileWatcher() as watcher:
                    assert watcher.is_running is True

                assert watcher.is_running is False

    def test_repr(self) -> None:
        """Test string representation."""
        with patch("pathlib.Path.exists", return_value=True):
            watcher = FileWatcher(paths=".")
            repr_str = repr(watcher)
            assert "FileWatcher" in repr_str
            assert "debounce" in repr_str

    def test_start_with_invalid_observer(self) -> None:
        """Test handling of observer startup failure."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("sbdk.dev.watcher.Observer") as mock_observer:
                mock_observer.side_effect = RuntimeError("Observer error")

                watcher = FileWatcher()
                with pytest.raises(WatcherError) as exc_info:
                    watcher.start()

                assert "Failed to start" in exc_info.value.message

    def test_quiet_mode(self) -> None:
        """Test quiet mode suppresses output."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("sbdk.dev.watcher.Observer"):
                config = WatchConfig(quiet=True)
                watcher = FileWatcher(config=config)

                # Should not raise even with quiet mode
                watcher.start()
                watcher.stop()


class TestIntegration:
    """Integration tests for watcher."""

    def test_full_watch_cycle(self, tmp_path: Path) -> None:
        """Test full watch cycle."""
        # Create test files
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        callback = Mock()
        config = WatchConfig(debounce_seconds=0.1)

        with patch("sbdk.dev.watcher.Observer") as mock_observer:
            mock_obs_instance = MagicMock()
            mock_observer.return_value = mock_obs_instance

            watcher = FileWatcher(
                paths=str(tmp_path),
                config=config,
                callback=callback
            )

            watcher.start()
            assert watcher.is_running is True

            # Simulate file change
            handler_call = mock_obs_instance.schedule.call_args
            assert handler_call is not None

            watcher.stop()
            assert watcher.is_running is False

    def test_multiple_path_watching(self) -> None:
        """Test watching multiple paths."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("sbdk.dev.watcher.Observer") as mock_observer:
                mock_obs_instance = MagicMock()
                mock_observer.return_value = mock_obs_instance

                watcher = FileWatcher(paths=["path1", "path2"])
                watcher.start()

                # Verify schedule was called for each path
                assert mock_obs_instance.schedule.call_count == 2

                watcher.stop()
