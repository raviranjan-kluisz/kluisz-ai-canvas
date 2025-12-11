"""Memory management for klx with dynamic loading.

This module automatically chooses between the full kluisz implementation
(when available) and the klx implementation (when standalone).
"""

from klx.utils.langflow_utils import has_kluisz_memory

# Import the appropriate implementation
if has_kluisz_memory():
    try:
        # Import full kluisz implementation
        from kluisz.memory import (
            aadd_messages,
            aadd_messagetables,
            add_messages,
            adelete_messages,
            aget_messages,
            astore_message,
            aupdate_messages,
            delete_message,
            delete_messages,
            get_messages,
            store_message,
        )
    except ImportError:
        # Fallback to klx implementation if kluisz import fails
        from klx.memory.stubs import (
            aadd_messages,
            aadd_messagetables,
            add_messages,
            adelete_messages,
            aget_messages,
            astore_message,
            aupdate_messages,
            delete_message,
            delete_messages,
            get_messages,
            store_message,
        )
else:
    # Use klx implementation
    from klx.memory.stubs import (
        aadd_messages,
        aadd_messagetables,
        add_messages,
        adelete_messages,
        aget_messages,
        astore_message,
        aupdate_messages,
        delete_message,
        delete_messages,
        get_messages,
        store_message,
    )

# Export the available functions
__all__ = [
    "aadd_messages",
    "aadd_messagetables",
    "add_messages",
    "adelete_messages",
    "aget_messages",
    "astore_message",
    "aupdate_messages",
    "delete_message",
    "delete_messages",
    "get_messages",
    "store_message",
]
