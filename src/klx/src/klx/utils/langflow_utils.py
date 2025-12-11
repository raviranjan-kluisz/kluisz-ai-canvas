"""Kluisz Kanvas environment utility functions."""

import importlib.util

from klx.log.logger import logger


class _KluiszModule:
    # Static variable
    # Tri-state:
    # - None: Kluisz Kanvas check not performed yet
    # - True: Kluisz Kanvas is available
    # - False: Kluisz Kanvas is not available
    _available = None

    @classmethod
    def is_available(cls):
        return cls._available

    @classmethod
    def set_available(cls, value):
        cls._available = value


def has_kluisz_memory():
    """Check if kluisz.memory (with database support) and MessageTable are available."""
    # TODO: REVISIT: Optimize this implementation later
    # - Consider refactoring to use lazy loading or a more robust service discovery mechanism
    #   that can handle runtime availability changes.

    # Use cached check from previous invocation (if applicable)

    is_kluisz_available = _KluiszModule.is_available()

    if is_kluisz_available is not None:
        return is_kluisz_available

    # First check (lazy load and cache check)

    module_spec = None

    try:
        module_spec = importlib.util.find_spec("kluisz")
    except ImportError:
        pass
    except (TypeError, ValueError) as e:
        logger.error(f"Error encountered checking for kluisz.memory: {e}")

    is_kluisz_available = module_spec is not None
    _KluiszModule.set_available(is_kluisz_available)

    return is_kluisz_available


# Backward compatibility alias
has_langflow_memory = has_kluisz_memory
