"""Data class for langflow - imports from klx.

This maintains backward compatibility while using the klx implementation.
"""

from klx.schema.data import Data, custom_serializer, serialize_data

__all__ = ["Data", "custom_serializer", "serialize_data"]
