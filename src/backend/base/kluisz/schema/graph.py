# Backwards compatibility module for kluisz.schema.graph
# This module redirects imports to the new klx.schema.graph module

from klx.schema.graph import InputValue, Tweaks

__all__ = ["InputValue", "Tweaks"]
