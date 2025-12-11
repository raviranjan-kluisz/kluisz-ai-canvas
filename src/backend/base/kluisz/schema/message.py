"""Message class for langflow - imports from klx.

This maintains backward compatibility while using the klx implementation.
"""

# Import and re-export to ensure class identity is preserved
from klx.schema.message import ContentBlock, DefaultModel, ErrorMessage, Message, MessageResponse

__all__ = ["ContentBlock", "DefaultModel", "ErrorMessage", "Message", "MessageResponse"]
