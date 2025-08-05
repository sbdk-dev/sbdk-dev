"""
Enhanced Visual Components for SBDK.dev CLI
Professional-grade components with real-time updates and proper state management

Author: SBDK.dev Team
Version: 2.0.0
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, Union

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class ComponentState(Enum):
    """Component state enumeration"""

    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ComponentConfig:
    """Configuration for visual components"""

    refresh_rate: float = 0.5  # seconds
    auto_update: bool = True
    show_timestamps: bool = True
    theme: str = "default"  # default, dark, light
    animations: bool = True


class BaseComponent:
    """Base class for all visual components"""

    def __init__(
        self,
        title: str = "",
        x: int = 0,
        y: int = 0,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        self.title = title
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.state = ComponentState.IDLE
        self.visible = True
        self.last_update = datetime.now()
        self.data: dict[str, Any] = {}
        self.callbacks: dict[str, list[Callable]] = {}

    def set_state(self, state: ComponentState, message: str = ""):
        """Update component state"""
        self.state = state
        self.data["state_message"] = message
        self.last_update = datetime.now()
        self._trigger_callback("state_changed", state, message)

    def set_data(self, key: str, value: Any):
        """Set component data"""
        self.data[key] = value
        self.last_update = datetime.now()
        self._trigger_callback("data_changed", key, value)

    def get_data(self, key: str, default=None):
        """Get component data"""
        return self.data.get(key, default)

    def on(self, event: str, callback: Callable):
        """Register event callback"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    def _trigger_callback(self, event: str, *args, **kwargs):
        """Trigger registered callbacks"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception:
                    pass  # Silently ignore callback errors

    def render(self) -> Panel:
        """Render the component (override in subclasses)"""
        return Panel(f"Base Component: {self.title}")


class StatusPanel(BaseComponent):
    """Enhanced status panel with real-time updates"""

    def __init__(self, title: str = "System Status", **kwargs):
        super().__init__(title, **kwargs)
        self.status_items: dict[str, dict[str, Any]] = {}

    def add_status_item(
        self,
        key: str,
        label: str,
        value: str,
        status: ComponentState = ComponentState.IDLE,
        icon: str = "●",
    ):
        """Add or update a status item"""
        self.status_items[key] = {
            "label": label,
            "value": value,
            "status": status,
            "icon": icon,
            "updated": datetime.now(),
        }
        self.last_update = datetime.now()

    def update_status_item(
        self, key: str, value: str, status: Optional[ComponentState] = None
    ):
        """Update an existing status item"""
        if key in self.status_items:
            self.status_items[key]["value"] = value
            self.status_items[key]["updated"] = datetime.now()
            if status:
                self.status_items[key]["status"] = status
            self.last_update = datetime.now()

    def get_status_color(self, status: ComponentState) -> str:
        """Get color for status"""
        colors = {
            ComponentState.IDLE: "white",
            ComponentState.LOADING: "yellow",
            ComponentState.SUCCESS: "green",
            ComponentState.ERROR: "red",
            ComponentState.WARNING: "orange",
        }
        return colors.get(status, "white")

    def render(self) -> Panel:
        """Render status panel"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", style="white", width=15)
        table.add_column("Details", style="white", width=30)
        table.add_column("Updated", style="dim", width=10)

        for _key, item in self.status_items.items():
            color = self.get_status_color(item["status"])
            icon = item["icon"]

            # Time since last update
            time_ago = datetime.now() - item["updated"]
            if time_ago.seconds < 60:
                time_str = f"{time_ago.seconds}s"
            elif time_ago.seconds < 3600:
                time_str = f"{time_ago.seconds // 60}m"
            else:
                time_str = f"{time_ago.seconds // 3600}h"

            table.add_row(
                f"{icon} {item['label']}",
                f"[{color}]{item['value']}[/{color}]",
                str(item.get("details", "")),
                time_str,
            )

        return Panel(table, title=f"📊 {self.title}", border_style="blue")


class PipelineProgressPanel(BaseComponent):
    """Pipeline execution progress with detailed steps"""

    def __init__(self, title: str = "Pipeline Progress", **kwargs):
        super().__init__(title, **kwargs)
        self.steps: list[dict[str, Any]] = []
        self.current_step = 0
        self.overall_progress = 0.0
        self.start_time: Optional[datetime] = None

    def add_step(self, name: str, description: str = "", estimated_duration: float = 0):
        """Add a pipeline step"""
        self.steps.append(
            {
                "name": name,
                "description": description,
                "estimated_duration": estimated_duration,
                "status": ComponentState.IDLE,
                "start_time": None,
                "end_time": None,
                "error_message": "",
                "progress": 0.0,
            }
        )

    def start_pipeline(self):
        """Start the pipeline execution"""
        self.start_time = datetime.now()
        self.current_step = 0
        self.overall_progress = 0.0
        for step in self.steps:
            step["status"] = ComponentState.IDLE
            step["start_time"] = None
            step["end_time"] = None
            step["progress"] = 0.0

    def start_step(self, step_index: int):
        """Start a specific step"""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self.steps[step_index]["status"] = ComponentState.LOADING
            self.steps[step_index]["start_time"] = datetime.now()
            self.last_update = datetime.now()

    def update_step_progress(self, step_index: int, progress: float):
        """Update step progress (0.0 to 1.0)"""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["progress"] = max(0.0, min(1.0, progress))
            self._calculate_overall_progress()
            self.last_update = datetime.now()

    def complete_step(
        self, step_index: int, success: bool = True, error_message: str = ""
    ):
        """Complete a step"""
        if 0 <= step_index < len(self.steps):
            step = self.steps[step_index]
            step["end_time"] = datetime.now()
            step["progress"] = 1.0
            step["status"] = ComponentState.SUCCESS if success else ComponentState.ERROR
            if error_message:
                step["error_message"] = error_message
            self._calculate_overall_progress()
            self.last_update = datetime.now()

    def _calculate_overall_progress(self):
        """Calculate overall pipeline progress"""
        if not self.steps:
            self.overall_progress = 0.0
            return

        total_progress = sum(step["progress"] for step in self.steps)
        self.overall_progress = total_progress / len(self.steps)

    def render(self) -> Panel:
        """Render pipeline progress"""
        content = Text()

        # Overall progress
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            content.append(f"⏱️  Elapsed: {elapsed.seconds}s  ", style="dim")

        progress_bar = "█" * int(self.overall_progress * 20)
        progress_bar += "░" * (20 - int(self.overall_progress * 20))
        content.append(
            f"Progress: [{progress_bar}] {self.overall_progress:.1%}\n\n", style="bold"
        )

        # Individual steps
        for i, step in enumerate(self.steps):
            status_icon = {
                ComponentState.IDLE: "⭕",
                ComponentState.LOADING: "🔄",
                ComponentState.SUCCESS: "✅",
                ComponentState.ERROR: "❌",
                ComponentState.WARNING: "⚠️",
            }.get(step["status"], "⭕")

            content.append(f"{status_icon} ", style="bold")

            if i == self.current_step:
                content.append(f"{step['name']}", style="bold yellow")
            elif step["status"] == ComponentState.SUCCESS:
                content.append(f"{step['name']}", style="green")
            elif step["status"] == ComponentState.ERROR:
                content.append(f"{step['name']}", style="red")
            else:
                content.append(f"{step['name']}", style="white")

            if step["description"]:
                content.append(f" - {step['description']}", style="dim")

            # Show progress for current step
            if step["status"] == ComponentState.LOADING and step["progress"] > 0:
                step_bar = "█" * int(step["progress"] * 10)
                step_bar += "░" * (10 - int(step["progress"] * 10))
                content.append(
                    f"\n    [{step_bar}] {step['progress']:.1%}", style="cyan"
                )

            # Show duration for completed steps
            if step["start_time"] and step["end_time"]:
                duration = step["end_time"] - step["start_time"]
                content.append(f" ({duration.seconds}s)", style="dim")

            # Show error message
            if step["error_message"]:
                content.append(f"\n    ❌ {step['error_message']}", style="red")

            content.append("\n")

        return Panel(content, title=f"🔄 {self.title}", border_style="yellow")


class LogPanel(BaseComponent):
    """Enhanced log viewer with filtering and search"""

    def __init__(self, title: str = "Activity Log", max_lines: int = 100, **kwargs):
        super().__init__(title, **kwargs)
        self.max_lines = max_lines
        self.log_entries: list[dict[str, Any]] = []
        self.filter_level: Optional[str] = None
        self.search_term: Optional[str] = None

    def add_log(
        self,
        message: str,
        level: str = "INFO",
        component: str = "",
        timestamp: Optional[datetime] = None,
    ):
        """Add a log entry"""
        entry = {
            "timestamp": timestamp or datetime.now(),
            "level": level.upper(),
            "component": component,
            "message": message,
        }

        self.log_entries.append(entry)

        # Keep only max_lines entries
        if len(self.log_entries) > self.max_lines:
            self.log_entries = self.log_entries[-self.max_lines :]

        self.last_update = datetime.now()
        self._trigger_callback("log_added", entry)

    def set_filter(
        self, level: Optional[str] = None, search_term: Optional[str] = None
    ):
        """Set log filtering"""
        self.filter_level = level
        self.search_term = search_term
        self.last_update = datetime.now()

    def get_level_color(self, level: str) -> str:
        """Get color for log level"""
        colors = {
            "DEBUG": "dim",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red",
        }
        return colors.get(level, "white")

    def _filter_logs(self) -> list[dict[str, Any]]:
        """Apply filtering to logs"""
        filtered = self.log_entries

        if self.filter_level:
            filtered = [log for log in filtered if log["level"] == self.filter_level]

        if self.search_term:
            filtered = [
                log
                for log in filtered
                if self.search_term.lower() in log["message"].lower()
            ]

        return filtered

    def render(self) -> Panel:
        """Render log panel"""
        content = Text()

        # Show filter status
        if self.filter_level or self.search_term:
            filter_info = []
            if self.filter_level:
                filter_info.append(f"Level: {self.filter_level}")
            if self.search_term:
                filter_info.append(f"Search: '{self.search_term}'")
            content.append(f"🔍 Filters: {', '.join(filter_info)}\n", style="cyan")
            content.append("─" * 50 + "\n", style="dim")

        # Show logs
        filtered_logs = self._filter_logs()

        if not filtered_logs:
            content.append("No log entries match current filters.", style="dim")
        else:
            # Show most recent logs first
            for log in filtered_logs[-20:]:  # Show last 20 entries
                time_str = log["timestamp"].strftime("%H:%M:%S")
                level_color = self.get_level_color(log["level"])

                content.append(f"[{time_str}] ", style="dim")
                content.append(f"{log['level']:<7} ", style=level_color)

                if log["component"]:
                    content.append(f"[{log['component']}] ", style="cyan")

                content.append(f"{log['message']}\n", style="white")

        return Panel(content, title=f"📋 {self.title}", border_style="green")


class MetricsPanel(BaseComponent):
    """Real-time metrics display with charts"""

    def __init__(self, title: str = "Performance Metrics", **kwargs):
        super().__init__(title, **kwargs)
        self.metrics: dict[str, dict[str, Any]] = {}

    def add_metric(
        self, key: str, name: str, unit: str = "", format_fn: Optional[Callable] = None
    ):
        """Add a metric to track"""
        self.metrics[key] = {
            "name": name,
            "unit": unit,
            "format_fn": format_fn or (lambda x: f"{x}"),
            "values": [],
            "timestamps": [],
            "current_value": 0,
            "min_value": float("inf"),
            "max_value": float("-inf"),
            "avg_value": 0,
        }

    def update_metric(self, key: str, value: Union[int, float]):
        """Update a metric value"""
        if key not in self.metrics:
            return

        metric = self.metrics[key]
        metric["current_value"] = value
        metric["values"].append(value)
        metric["timestamps"].append(datetime.now())

        # Keep only last 100 values
        if len(metric["values"]) > 100:
            metric["values"] = metric["values"][-100:]
            metric["timestamps"] = metric["timestamps"][-100:]

        # Update stats
        metric["min_value"] = min(metric["values"])
        metric["max_value"] = max(metric["values"])
        metric["avg_value"] = sum(metric["values"]) / len(metric["values"])

        self.last_update = datetime.now()

    def render(self) -> Panel:
        """Render metrics panel"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="white", width=20)
        table.add_column("Current", style="bold green", width=12)
        table.add_column("Min", style="blue", width=10)
        table.add_column("Max", style="red", width=10)
        table.add_column("Avg", style="yellow", width=10)
        table.add_column("Trend", style="cyan", width=15)

        for _key, metric in self.metrics.items():
            current = metric["format_fn"](metric["current_value"])
            min_val = (
                metric["format_fn"](metric["min_value"])
                if metric["min_value"] != float("inf")
                else "N/A"
            )
            max_val = (
                metric["format_fn"](metric["max_value"])
                if metric["max_value"] != float("-inf")
                else "N/A"
            )
            avg_val = (
                metric["format_fn"](metric["avg_value"]) if metric["values"] else "N/A"
            )

            # Simple trend indicator
            if len(metric["values"]) >= 2:
                if metric["values"][-1] > metric["values"][-2]:
                    trend = "📈 Up"
                elif metric["values"][-1] < metric["values"][-2]:
                    trend = "📉 Down"
                else:
                    trend = "➡️ Stable"
            else:
                trend = "➖ No data"

            table.add_row(
                f"{metric['name']} {metric['unit']}",
                current,
                min_val,
                max_val,
                avg_val,
                trend,
            )

        return Panel(table, title=f"📈 {self.title}", border_style="magenta")


class ActionPanel(BaseComponent):
    """Interactive action panel with buttons and commands"""

    def __init__(self, title: str = "Quick Actions", **kwargs):
        super().__init__(title, **kwargs)
        self.actions: list[dict[str, Any]] = []

    def add_action(
        self,
        key: str,
        label: str,
        description: str = "",
        callback: Optional[Callable] = None,
        enabled: bool = True,
    ):
        """Add an action button"""
        self.actions.append(
            {
                "key": key,
                "label": label,
                "description": description,
                "callback": callback,
                "enabled": enabled,
                "last_used": None,
            }
        )

    def trigger_action(self, key: str) -> bool:
        """Trigger an action by key"""
        for action in self.actions:
            if action["key"] == key and action["enabled"]:
                action["last_used"] = datetime.now()
                if action["callback"]:
                    try:
                        action["callback"]()
                        return True
                    except Exception:
                        return False
        return False

    def set_action_enabled(self, key: str, enabled: bool):
        """Enable/disable an action"""
        for action in self.actions:
            if action["key"] == key:
                action["enabled"] = enabled
                break

    def render(self) -> Panel:
        """Render action panel"""
        content = Text()
        content.append("🎮 Available Actions:\n\n", style="bold cyan")

        for action in self.actions:
            if action["enabled"]:
                style = "bold green"
                prefix = "✓"
            else:
                style = "dim"
                prefix = "✗"

            content.append(f"{prefix} ", style=style)
            content.append(f"[{action['key']}]", style="bold white")
            content.append(f" {action['label']}", style=style)

            if action["description"]:
                content.append(f"\n    {action['description']}", style="dim")

            if action["last_used"]:
                time_ago = datetime.now() - action["last_used"]
                if time_ago.seconds < 60:
                    content.append(f" (used {time_ago.seconds}s ago)", style="dim")

            content.append("\n")

        return Panel(content, title=f"🎯 {self.title}", border_style="cyan")


# Factory functions for quick component creation


def create_server_status_panel() -> StatusPanel:
    """Create a pre-configured server status panel"""
    panel = StatusPanel("Server Status")
    panel.add_status_item(
        "fastapi", "FastAPI Server", "Unknown", ComponentState.IDLE, "🌐"
    )
    panel.add_status_item("database", "DuckDB", "Unknown", ComponentState.IDLE, "🦆")
    panel.add_status_item(
        "filewatch", "File Watcher", "Unknown", ComponentState.IDLE, "👁️"
    )
    panel.add_status_item(
        "pipeline", "Last Pipeline", "Not run", ComponentState.IDLE, "🔄"
    )
    return panel


def create_pipeline_progress() -> PipelineProgressPanel:
    """Create a pre-configured pipeline progress panel"""
    panel = PipelineProgressPanel("Pipeline Execution")
    panel.add_step("users", "Generate user data", 5.0)
    panel.add_step("events", "Process event logs", 3.0)
    panel.add_step("orders", "Analyze order data", 4.0)
    panel.add_step("dbt_run", "Execute dbt models", 8.0)
    panel.add_step("dbt_test", "Run dbt tests", 2.0)
    return panel


def create_activity_log() -> LogPanel:
    """Create a pre-configured activity log"""
    panel = LogPanel("Activity Log", max_lines=200)
    return panel


def create_performance_metrics() -> MetricsPanel:
    """Create a pre-configured performance metrics panel"""
    panel = MetricsPanel("Performance Metrics")
    panel.add_metric("records_per_sec", "Records/sec", "rec/s", lambda x: f"{x:.0f}")
    panel.add_metric("memory_usage", "Memory Usage", "MB", lambda x: f"{x:.1f}")
    panel.add_metric("cpu_usage", "CPU Usage", "%", lambda x: f"{x:.1f}")
    panel.add_metric("response_time", "Response Time", "ms", lambda x: f"{x:.0f}")
    return panel


def create_quick_actions() -> ActionPanel:
    """Create a pre-configured quick actions panel"""
    panel = ActionPanel("Quick Actions")
    panel.add_action("r", "Run Pipeline", "Execute the full data pipeline")
    panel.add_action(
        "a", "Toggle Auto-run", "Enable/disable automatic pipeline execution"
    )
    panel.add_action("s", "Show Status", "Display detailed system status")
    panel.add_action("l", "View Logs", "Open the activity log viewer")
    panel.add_action("c", "Configuration", "Edit project configuration")
    panel.add_action("h", "Help", "Show help and documentation")
    return panel
