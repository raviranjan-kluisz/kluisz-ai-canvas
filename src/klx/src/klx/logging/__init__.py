"""Backwards compatibility module for klx.logging.

This module provides backwards compatibility for code that imports from klx.logging.
All functionality has been moved to klx.log.
"""

# Re-export everything from klx.log for backwards compatibility
from klx.log.logger import configure, logger

# Maintain the same __all__ exports
__all__ = ["configure", "logger"]
