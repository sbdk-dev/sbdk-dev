"""
Double-Buffered Terminal Renderer

Provides flicker-free updates using double buffering and intelligent cursor positioning.
Optimized for smooth 30-60 FPS rendering with minimal terminal operations.
"""

import os
import shutil
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class TerminalState:
    """Current terminal state tracking"""

    width: int = 80
    height: int = 24
    cursor_x: int = 0
    cursor_y: int = 0
    alternate_screen: bool = False


class VisualRenderer:
    """
    High-performance terminal renderer with double buffering.

    Features:
    - Double buffering to prevent flicker
    - Intelligent diff-based updates
    - Cursor optimization
    - 30-60 FPS rendering capability
    - Cross-platform terminal support
    """

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.frame_time = 1.0 / fps
        self.terminal = TerminalState()
        self.front_buffer: list[str] = []
        self.back_buffer: list[str] = []
        self.running = False
        self.render_thread = None
        self.components: list[Any] = []
        self.dirty_regions: set = set()

        # Terminal capabilities
        self.supports_color = self._detect_color_support()
        self.supports_unicode = self._detect_unicode_support()

        # ANSI escape sequences
        self.CLEAR_SCREEN = "\033[2J"
        self.HIDE_CURSOR = "\033[?25l"
        self.SHOW_CURSOR = "\033[?25h"
        self.HOME_CURSOR = "\033[H"
        self.ALT_SCREEN_ON = "\033[?1049h"
        self.ALT_SCREEN_OFF = "\033[?1049l"

        self._setup_terminal()

    def _detect_color_support(self) -> bool:
        """Detect if terminal supports colors"""
        return (
            os.getenv("COLORTERM") in ("truecolor", "24bit")
            or os.getenv("TERM", "").endswith("256color")
            or os.getenv("TERM") == "xterm-color"
        )

    def _detect_unicode_support(self) -> bool:
        """Detect if terminal supports Unicode box drawing"""
        try:
            # Test Unicode support
            sys.stdout.write("─")
            sys.stdout.flush()
            return True
        except UnicodeEncodeError:
            return False

    def _setup_terminal(self):
        """Initialize terminal for optimal rendering"""
        if not sys.stdout.isatty():
            return

        # Get terminal size
        size = shutil.get_terminal_size()
        self.terminal.width = size.columns
        self.terminal.height = size.lines

        # Initialize buffers
        self._resize_buffers()

        # Setup signal handling for resize
        import signal

        signal.signal(signal.SIGWINCH, self._handle_resize)

    def _resize_buffers(self):
        """Resize internal buffers to match terminal"""
        empty_line = " " * self.terminal.width
        buffer_size = self.terminal.height

        self.front_buffer = [empty_line] * buffer_size
        self.back_buffer = [empty_line] * buffer_size
        self.dirty_regions = set(range(buffer_size))

    def _handle_resize(self, signum, frame):
        """Handle terminal resize events"""
        size = shutil.get_terminal_size()
        self.terminal.width = size.columns
        self.terminal.height = size.lines
        self._resize_buffers()

    def enter_alternate_screen(self):
        """Enter alternate screen buffer for full-screen apps"""
        if sys.stdout.isatty():
            sys.stdout.write(self.ALT_SCREEN_ON)
            sys.stdout.write(self.HIDE_CURSOR)
            sys.stdout.flush()
            self.terminal.alternate_screen = True

    def exit_alternate_screen(self):
        """Exit alternate screen buffer"""
        if sys.stdout.isatty() and self.terminal.alternate_screen:
            sys.stdout.write(self.SHOW_CURSOR)
            sys.stdout.write(self.ALT_SCREEN_OFF)
            sys.stdout.flush()
            self.terminal.alternate_screen = False

    def clear_screen(self):
        """Clear entire screen"""
        if sys.stdout.isatty():
            sys.stdout.write(self.CLEAR_SCREEN)
            sys.stdout.write(self.HOME_CURSOR)
            sys.stdout.flush()

    def move_cursor(self, x: int, y: int):
        """Move cursor to specific position"""
        if sys.stdout.isatty():
            sys.stdout.write(f"\033[{y+1};{x+1}H")
            self.terminal.cursor_x = x
            self.terminal.cursor_y = y

    def write_at(self, x: int, y: int, text: str):
        """Write text at specific position in back buffer"""
        if 0 <= y < len(self.back_buffer):
            line = self.back_buffer[y]
            if x < len(line):
                # Replace text in line
                before = line[:x]
                after = line[x + len(text) :] if x + len(text) < len(line) else ""
                self.back_buffer[y] = before + text + after
                self.dirty_regions.add(y)

    def write_line(self, y: int, text: str):
        """Write entire line to back buffer"""
        if 0 <= y < len(self.back_buffer):
            # Pad or truncate to terminal width
            padded_text = text.ljust(self.terminal.width)[: self.terminal.width]
            self.back_buffer[y] = padded_text
            self.dirty_regions.add(y)

    def add_component(self, component):
        """Add a component to be rendered"""
        self.components.append(component)

    def remove_component(self, component):
        """Remove a component from rendering"""
        if component in self.components:
            self.components.remove(component)

    def render_components(self):
        """Render all components to back buffer"""
        # Clear back buffer
        empty_line = " " * self.terminal.width
        self.back_buffer = [empty_line] * self.terminal.height

        # Render each component
        for component in self.components:
            if hasattr(component, "render"):
                component.render(self)

    def swap_buffers(self):
        """Swap front and back buffers and update screen"""
        if not sys.stdout.isatty():
            # For non-TTY, just print the lines
            for line in self.back_buffer:
                print(line.rstrip())
            return

        # Update only dirty regions for performance
        for line_num in self.dirty_regions:
            if line_num < len(self.back_buffer):
                front_line = (
                    self.front_buffer[line_num]
                    if line_num < len(self.front_buffer)
                    else ""
                )
                back_line = self.back_buffer[line_num]

                if front_line != back_line:
                    self.move_cursor(0, line_num)
                    sys.stdout.write(back_line)

        sys.stdout.flush()

        # Swap buffers
        self.front_buffer, self.back_buffer = self.back_buffer, self.front_buffer
        self.dirty_regions.clear()

    def start_render_loop(self):
        """Start the main render loop in a separate thread"""
        if self.running:
            return

        self.running = True
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()

    def stop_render_loop(self):
        """Stop the render loop"""
        self.running = False
        if self.render_thread:
            self.render_thread.join(timeout=1.0)

    def _render_loop(self):
        """Main render loop - runs in separate thread"""
        last_frame_time = time.time()

        while self.running:
            current_time = time.time()
            delta_time = current_time - last_frame_time

            if delta_time >= self.frame_time:
                self.render_components()
                self.swap_buffers()
                last_frame_time = current_time
            else:
                # Sleep until next frame
                sleep_time = self.frame_time - delta_time
                time.sleep(max(0, sleep_time))

    def render_frame(self):
        """Render a single frame (for manual control)"""
        self.render_components()
        self.swap_buffers()

    def get_terminal_size(self) -> tuple:
        """Get current terminal dimensions"""
        return (self.terminal.width, self.terminal.height)

    def supports_feature(self, feature: str) -> bool:
        """Check if terminal supports specific features"""
        features = {
            "color": self.supports_color,
            "unicode": self.supports_unicode,
            "tty": sys.stdout.isatty(),
        }
        return features.get(feature, False)
