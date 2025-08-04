"""
Visual CLI Application Framework

Main application class that orchestrates the visual CLI components.
Provides React-like app structure with automatic rendering and event handling.
"""

import signal
import sys
import threading
import time
from typing import Any, Callable, Optional

from .components import Component, Footer, Header
from .renderer import VisualRenderer


class VisualApp:
    """
    Main Visual CLI Application

    Provides a React-like application framework for terminal UIs with:
    - Component management
    - Event handling
    - Automatic rendering
    - Lifecycle management
    """

    def __init__(self, title: str = "SBDK Visual CLI", fps: int = 30):
        self.title = title
        self.renderer = VisualRenderer(fps=fps)
        self.components: list[Component] = []
        self.running = False
        self.event_handlers: dict[str, list[Callable]] = {}
        self.state: dict[str, Any] = {}

        # Default components
        self.header: Optional[Header] = None
        self.footer: Optional[Footer] = None

        # Setup signal handling
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def set_header(
        self, title: str = None, status: str = "Ready", show_time: bool = True, **kwargs
    ) -> Header:
        """Add or update header component"""
        if self.header:
            self.remove_component(self.header)

        self.header = Header(
            title=title or self.title, status=status, show_time=show_time, **kwargs
        )
        self.add_component(self.header)
        return self.header

    def set_footer(
        self, help_text: str = "Press 'q' to quit", status: str = "", **kwargs
    ) -> Footer:
        """Add or update footer component"""
        if self.footer:
            self.remove_component(self.footer)

        self.footer = Footer(help_text=help_text, status=status, **kwargs)
        self.add_component(self.footer)
        return self.footer

    def add_component(self, component: Component):
        """Add a component to the application"""
        self.components.append(component)
        self.renderer.add_component(component)
        component.mount()

    def remove_component(self, component: Component):
        """Remove a component from the application"""
        if component in self.components:
            component.unmount()
            self.components.remove(component)
            self.renderer.remove_component(component)

    def get_component_by_type(self, component_type: type) -> Optional[Component]:
        """Get first component of specified type"""
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None

    def set_state(self, new_state: dict[str, Any]):
        """Update application state"""
        self.state.update(new_state)

    def get_state(self, key: str, default=None):
        """Get application state value"""
        return self.state.get(key, default)

    def on(self, event: str, handler: Callable):
        """Register event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def emit(self, event: str, *args, **kwargs):
        """Emit event to registered handlers"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    print(f"Error in event handler: {e}", file=sys.stderr)

    def update_header_status(self, status: str):
        """Quick update of header status"""
        if self.header:
            self.header.status = status

    def update_footer_status(self, status: str):
        """Quick update of footer status"""
        if self.footer:
            self.footer.status = status

    def start(self, use_alternate_screen: bool = True):
        """Start the visual application"""
        if self.running:
            return

        try:
            self.running = True

            if use_alternate_screen:
                self.renderer.enter_alternate_screen()

            # Start render loop
            self.renderer.start_render_loop()

            # Emit start event
            self.emit("start")

            # Initial render
            self.renderer.render_frame()

        except Exception as e:
            self.stop()
            raise e

    def stop(self):
        """Stop the visual application"""
        if not self.running:
            return

        self.running = False

        # Emit stop event
        self.emit("stop")

        # Stop rendering
        self.renderer.stop_render_loop()

        # Exit alternate screen
        self.renderer.exit_alternate_screen()

        # Unmount all components
        for component in self.components[
            :
        ]:  # Copy list to avoid modification during iteration
            component.unmount()

    def render_once(self):
        """Render a single frame (for non-interactive use)"""
        self.renderer.render_frame()

    def run_until_keypress(self, exit_keys: list[str] = None):
        """Run application until specific key is pressed"""
        if exit_keys is None:
            exit_keys = ["q", "Q", "\x03"]  # q, Q, or Ctrl+C

        try:
            # Setup terminal for raw input
            if sys.stdin.isatty():
                import termios
                import tty

                old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())

            while self.running:
                if sys.stdin.isatty():
                    # Check for input without blocking
                    import select

                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        if key in exit_keys:
                            break
                        self.emit("keypress", key)
                else:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            if sys.stdin.isatty():
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.stop()

    def run_for_duration(self, duration: float):
        """Run application for specified duration in seconds"""
        import time

        start_time = time.time()

        try:
            while self.running and (time.time() - start_time) < duration:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signals"""
        self.emit("interrupt", signum)
        self.stop()

    def create_layout(self, layout_type: str = "default") -> dict[str, Any]:
        """Create a standard layout with predefined areas"""
        width, height = self.renderer.get_terminal_size()

        if layout_type == "default":
            return {
                "header": {"y": 0, "height": 3},
                "content": {"y": 3, "height": height - 5},
                "footer": {"y": height - 2, "height": 2},
                "full_width": width,
                "content_width": width,
            }
        elif layout_type == "dashboard":
            return {
                "header": {"y": 0, "height": 3},
                "sidebar": {"x": 0, "y": 3, "width": 25, "height": height - 5},
                "main": {"x": 25, "y": 3, "width": width - 25, "height": height - 5},
                "footer": {"y": height - 2, "height": 2},
                "full_width": width,
            }
        else:
            raise ValueError(f"Unknown layout type: {layout_type}")

    def debug_info(self) -> dict[str, Any]:
        """Get debug information about the application"""
        return {
            "running": self.running,
            "components": len(self.components),
            "terminal_size": self.renderer.get_terminal_size(),
            "supports_color": self.renderer.supports_feature("color"),
            "supports_unicode": self.renderer.supports_feature("unicode"),
            "is_tty": self.renderer.supports_feature("tty"),
            "fps": self.renderer.fps,
            "state": self.state,
        }


# Convenience functions for quick usage


def create_simple_app(
    title: str = "SBDK CLI", show_header: bool = True, show_footer: bool = True
) -> VisualApp:
    """Create a simple app with header and footer"""
    app = VisualApp(title=title)

    if show_header:
        app.set_header()

    if show_footer:
        app.set_footer()

    return app


def quick_demo():
    """Quick demonstration of visual CLI capabilities"""
    import time

    from .components import Box, ProgressBar, Spinner

    app = create_simple_app("SBDK Visual CLI Demo")

    # Create layout
    layout = app.create_layout("default")

    # Add demo components
    progress = ProgressBar(
        x=5, y=layout["content"]["y"] + 2, width=40, label="Processing"
    )

    spinner = Spinner(
        x=5, y=layout["content"]["y"] + 4, style="dots", label="Loading modules"
    )

    info_box = Box(
        x=5,
        y=layout["content"]["y"] + 6,
        width=50,
        height=8,
        title="System Status",
        border=True,
    )
    info_box.set_content(
        [
            "✓ Visual CLI Framework: Active",
            "✓ Double Buffering: Enabled",
            "✓ Unicode Support: "
            + ("Yes" if app.renderer.supports_feature("unicode") else "No"),
            "✓ Color Support: "
            + ("Yes" if app.renderer.supports_feature("color") else "No"),
            "",
            "Press 'q' to quit demo",
        ]
    )

    app.add_component(progress)
    app.add_component(spinner)
    app.add_component(info_box)

    # Progress animation
    def animate_progress():
        for i in range(101):
            progress.set_progress(i / 100.0)
            time.sleep(0.05)

    # Start app
    app.start()

    # Run progress animation in background
    progress_thread = threading.Thread(target=animate_progress, daemon=True)
    progress_thread.start()

    # Run until user quits
    app.run_until_keypress(["q", "Q"])


if __name__ == "__main__":
    quick_demo()
