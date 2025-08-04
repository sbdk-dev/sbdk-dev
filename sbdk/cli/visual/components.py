"""
Visual CLI Components

React-like components for building modern terminal UIs.
Includes Header, Footer, ProgressBar, Spinner, Box, and ContentArea components.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Optional


class Component(ABC):
    """Base component class with React-like lifecycle"""

    def __init__(self, x: int = 0, y: int = 0, width: int = None, height: int = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.focused = False
        self.mounted = False
        self.state = {}
        self.children: list[Component] = []
        self.parent: Optional[Component] = None

    def set_state(self, new_state: dict[str, Any]):
        """Update component state (triggers re-render)"""
        self.state.update(new_state)

    def add_child(self, child: "Component"):
        """Add child component"""
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: "Component"):
        """Remove child component"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    @abstractmethod
    def render(self, renderer):
        """Render component to the renderer"""
        pass

    def mount(self):
        """Called when component is mounted"""
        self.mounted = True

    def unmount(self):
        """Called when component is unmounted"""
        self.mounted = False


class Header(Component):
    """Header component with title, status, and timestamp"""

    def __init__(
        self,
        title: str = "SBDK Analytics",
        status: str = "Ready",
        show_time: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.title = title
        self.status = status
        self.show_time = show_time
        self.border_style = "single"  # single, double, rounded

    def render(self, renderer):
        if not self.visible:
            return

        width, height = renderer.get_terminal_size()

        # Box drawing characters
        if renderer.supports_feature("unicode"):
            if self.border_style == "double":
                h_line, v_line = "═", "║"
                tl, tr, bl, br = "╔", "╗", "╚", "╝"
            elif self.border_style == "rounded":
                h_line, v_line = "─", "│"
                tl, tr, bl, br = "╭", "╮", "╰", "╯"
            else:  # single
                h_line, v_line = "─", "│"
                tl, tr, bl, br = "┌", "┐", "└", "┘"
        else:
            h_line, v_line = "-", "|"
            tl, tr, bl, br = "+", "+", "+", "+"

        # Top border
        top_line = tl + h_line * (width - 2) + tr
        renderer.write_line(0, top_line)

        # Title line with status and time
        title_content = f" {self.title} "
        status_content = f" [{self.status}] "

        if self.show_time:
            current_time = time.strftime("%H:%M:%S")
            time_content = f" {current_time} "
        else:
            time_content = ""

        # Calculate spacing
        available_width = width - 2  # Account for side borders
        title_len = len(title_content)
        status_len = len(status_content)
        time_len = len(time_content)

        if title_len + status_len + time_len <= available_width:
            # Everything fits
            middle_space = available_width - title_len - status_len - time_len
            title_line = (
                v_line
                + title_content
                + " " * middle_space
                + status_content
                + time_content
                + v_line
            )
        else:
            # Truncate title if needed
            remaining = available_width - status_len - time_len - 3  # 3 for "..."
            if remaining > 0:
                truncated_title = title_content[:remaining] + "..."
                title_line = (
                    v_line + truncated_title + status_content + time_content + v_line
                )
            else:
                title_line = v_line + " " * available_width + v_line

        renderer.write_line(1, title_line)

        # Bottom border
        bottom_line = bl + h_line * (width - 2) + br
        renderer.write_line(2, bottom_line)


class Footer(Component):
    """Footer component with help text and status"""

    def __init__(
        self, help_text: str = "Press 'q' to quit", status: str = "", **kwargs
    ):
        super().__init__(**kwargs)
        self.help_text = help_text
        self.status = status
        self.border_style = "single"

    def render(self, renderer):
        if not self.visible:
            return

        width, height = renderer.get_terminal_size()
        footer_y = height - 2  # Position at bottom

        # Box drawing characters
        if renderer.supports_feature("unicode"):
            h_line, v_line = "─", "│"
            tl, tr, _bl, _br = "┌", "┐", "└", "┘"
        else:
            h_line, v_line = "-", "|"
            tl, tr, _bl, _br = "+", "+", "+", "+"

        # Top border of footer
        top_line = tl + h_line * (width - 2) + tr
        renderer.write_line(footer_y, top_line)

        # Content line
        content = f" {self.help_text} "
        if self.status:
            status_content = f" {self.status} "
            available = width - 2 - len(content)
            if len(status_content) <= available:
                spacing = available - len(status_content)
                content_line = (
                    v_line + content + " " * spacing + status_content + v_line
                )
            else:
                content_line = (
                    v_line + content + " " * (width - 2 - len(content)) + v_line
                )
        else:
            padding = width - 2 - len(content)
            content_line = v_line + content + " " * padding + v_line

        renderer.write_line(footer_y + 1, content_line)


class ProgressBar(Component):
    """Animated progress bar component"""

    def __init__(
        self,
        progress: float = 0.0,
        width: int = 40,
        label: str = "",
        style: str = "modern",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.progress = max(0.0, min(1.0, progress))
        self.bar_width = width
        self.label = label
        self.style = style  # modern, classic, blocks
        self.animation_offset = 0

    def set_progress(self, progress: float):
        """Update progress value"""
        self.progress = max(0.0, min(1.0, progress))

    def render(self, renderer):
        if not self.visible:
            return

        # Animation for visual appeal
        self.animation_offset = (self.animation_offset + 1) % 8

        if self.style == "modern" and renderer.supports_feature("unicode"):
            # Modern style with Unicode blocks
            filled_char = "█"
            partial_chars = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]
            empty_char = "░"
        elif self.style == "blocks" and renderer.supports_feature("unicode"):
            # Block style
            filled_char = "■"
            partial_chars = ["", "▪"]
            empty_char = "□"
        else:
            # Classic ASCII style
            filled_char = "#"
            partial_chars = ["", "."]
            empty_char = "-"

        # Calculate filled portion
        filled_width = self.progress * self.bar_width
        filled_blocks = int(filled_width)
        partial_block = filled_width - filled_blocks

        # Build progress bar
        bar = filled_char * filled_blocks

        if partial_block > 0 and filled_blocks < self.bar_width:
            if partial_chars:
                partial_index = int(partial_block * len(partial_chars))
                bar += partial_chars[min(partial_index, len(partial_chars) - 1)]
                filled_blocks += 1

        remaining = self.bar_width - len(bar)
        bar += empty_char * remaining

        # Format with percentage
        percentage = int(self.progress * 100)
        if self.label:
            output = f"{self.label}: [{bar}] {percentage}%"
        else:
            output = f"[{bar}] {percentage}%"

        renderer.write_at(self.x, self.y, output)


class Spinner(Component):
    """Loading spinner component"""

    def __init__(self, style: str = "dots", label: str = "Loading", **kwargs):
        super().__init__(**kwargs)
        self.style = style
        self.label = label
        self.frame = 0

        # Spinner styles
        self.styles = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "line": ["-", "\\", "|", "/"],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "bounce": ["⠁", "⠂", "⠄", "⠂"],
            "clock": [
                "🕐",
                "🕑",
                "🕒",
                "🕓",
                "🕔",
                "🕕",
                "🕖",
                "🕗",
                "🕘",
                "🕙",
                "🕚",
                "🕛",
            ],
            "classic": ["|", "/", "-", "\\"],
        }

        # Style will be checked in render method when renderer is available

    def render(self, renderer):
        if not self.visible:
            return

        # Use classic style for non-Unicode terminals
        if not renderer.supports_feature("unicode"):
            if self.style not in ["line", "classic"]:
                self.style = "classic"

        frames = self.styles.get(self.style, self.styles["classic"])
        current_frame = frames[self.frame % len(frames)]

        output = f"{current_frame} {self.label}"
        renderer.write_at(self.x, self.y, output)

        # Advance animation
        self.frame += 1


class Box(Component):
    """Flexible container component with borders and content"""

    def __init__(
        self,
        border: bool = True,
        title: str = "",
        border_style: str = "single",
        padding: int = 1,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.border = border
        self.title = title
        self.border_style = border_style
        self.padding = padding
        self.content_lines: list[str] = []

    def set_content(self, lines: list[str]):
        """Set content lines for the box"""
        self.content_lines = lines

    def add_line(self, line: str):
        """Add a line to the content"""
        self.content_lines.append(line)

    def clear_content(self):
        """Clear all content"""
        self.content_lines.clear()

    def render(self, renderer):
        if not self.visible:
            return

        width, height = renderer.get_terminal_size()
        box_width = self.width or width
        box_height = self.height or (height - self.y)

        if self.border:
            # Box drawing characters
            if renderer.supports_feature("unicode"):
                if self.border_style == "double":
                    h_line, v_line = "═", "║"
                    tl, tr, bl, br = "╔", "╗", "╚", "╝"
                elif self.border_style == "rounded":
                    h_line, v_line = "─", "│"
                    tl, tr, bl, br = "╭", "╮", "╰", "╯"
                else:  # single
                    h_line, v_line = "─", "│"
                    tl, tr, bl, br = "┌", "┐", "└", "┘"
            else:
                h_line, v_line = "-", "|"
                tl, tr, bl, br = "+", "+", "+", "+"

            # Top border
            if self.title:
                title_len = len(self.title)
                if title_len + 4 < box_width:  # 4 for "[ ]"
                    title_part = f"[ {self.title} ]"
                    remaining = box_width - 2 - len(title_part)
                    left_line = h_line * (remaining // 2)
                    right_line = h_line * (remaining - len(left_line))
                    top_line = tl + left_line + title_part + right_line + tr
                else:
                    top_line = tl + h_line * (box_width - 2) + tr
            else:
                top_line = tl + h_line * (box_width - 2) + tr

            renderer.write_line(self.y, top_line)

            # Content area with side borders
            content_width = box_width - 2 - (2 * self.padding)
            content_start_y = self.y + 1
            content_height = box_height - 2

            for i in range(content_height):
                line_y = content_start_y + i

                if i < len(self.content_lines):
                    content = self.content_lines[i]
                    # Truncate or pad content
                    if len(content) > content_width:
                        content = content[: content_width - 3] + "..."
                    content = content.ljust(content_width)
                else:
                    content = " " * content_width

                padding_str = " " * self.padding
                line = v_line + padding_str + content + padding_str + v_line
                renderer.write_line(line_y, line)

            # Bottom border
            bottom_line = bl + h_line * (box_width - 2) + br
            renderer.write_line(self.y + box_height - 1, bottom_line)
        else:
            # No border, just content
            content_width = box_width - (2 * self.padding)
            for i, line in enumerate(self.content_lines):
                if i >= box_height:
                    break
                line_y = self.y + i
                content = line[:content_width] if len(line) > content_width else line
                padding_str = " " * self.padding
                renderer.write_line(line_y, padding_str + content)


class ContentArea(Component):
    """Scrollable content area component"""

    def __init__(self, lines: list[str] = None, scroll_y: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.lines = lines or []
        self.scroll_y = scroll_y
        self.max_scroll = 0

    def set_lines(self, lines: list[str]):
        """Set content lines"""
        self.lines = lines
        self.max_scroll = max(0, len(lines) - (self.height or 10))

    def scroll_up(self, amount: int = 1):
        """Scroll content up"""
        self.scroll_y = max(0, self.scroll_y - amount)

    def scroll_down(self, amount: int = 1):
        """Scroll content down"""
        self.scroll_y = min(self.max_scroll, self.scroll_y + amount)

    def render(self, renderer):
        if not self.visible:
            return

        width, height = renderer.get_terminal_size()
        area_width = self.width or width
        area_height = self.height or height

        # Render visible lines
        for i in range(area_height):
            line_index = self.scroll_y + i
            if line_index < len(self.lines):
                line = self.lines[line_index]
                # Truncate line if too long
                if len(line) > area_width:
                    line = line[: area_width - 3] + "..."
                renderer.write_line(self.y + i, line)
            else:
                # Empty line
                renderer.write_line(self.y + i, " " * area_width)
