"""
SBDK Visual CLI Module

A modern, interactive CLI framework with React-like components for terminal UIs.
Provides smooth in-place updates, rich visual elements, and responsive layouts.
"""

from .app import VisualApp
from .components import Box, ContentArea, Footer, Header, ProgressBar, Spinner
from .renderer import VisualRenderer

__all__ = [
    "VisualRenderer",
    "Header",
    "Footer",
    "ProgressBar",
    "Spinner",
    "Box",
    "ContentArea",
    "VisualApp",
]

__version__ = "1.0.1"
