"""Backwards compatibility module for klx.logging.logger.

This module provides backwards compatibility for code that imports from klx.logging.logger.
All functionality has been moved to klx.log.logger.
"""

# Ensure we maintain all the original exports
from klx.log.logger import (
    InterceptHandler,
    LogConfig,
    configure,
    logger,
    setup_gunicorn_logger,
    setup_uvicorn_logger,
)

__all__ = [
    "InterceptHandler",
    "LogConfig",
    "configure",
    "logger",
    "setup_gunicorn_logger",
    "setup_uvicorn_logger",
]
