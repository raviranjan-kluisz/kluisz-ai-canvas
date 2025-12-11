from collections.abc import AsyncIterator, Generator, Iterator
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
from typing import Any, cast
from uuid import UUID

import numpy as np
import pandas as pd
from langchain_core.documents import Document
from klx.log.logger import logger
from pydantic import BaseModel
from pydantic.v1 import BaseModel as BaseModelV1

from kluisz.serialization.constants import MAX_ITEMS_LENGTH, MAX_TEXT_LENGTH
from kluisz.services.deps import get_settings_service

# Try to import SQLModel for type checking
try:
    from sqlmodel import SQLModel as SQLModelType
except ImportError:
    SQLModelType = None


# Sentinel variable to signal a failed serialization.
# Using a helper class ensures that the sentinel is a unique object,
# while its __repr__ displays the desired message.
class _UnserializableSentinel:
    def __repr__(self):
        return "[Unserializable Object]"


UNSERIALIZABLE_SENTINEL = _UnserializableSentinel()


@lru_cache(maxsize=1)
def get_max_text_length() -> int:
    """Return the maximum allowed text length for serialization from the current settings."""
    return get_settings_service().settings.max_text_length


@lru_cache(maxsize=1)
def get_max_items_length() -> int:
    """Return the maximum allowed number of items for serialization, as defined in the current settings."""
    return get_settings_service().settings.max_items_length


def _serialize_str(obj: str, max_length: int | None, _) -> str:
    """Truncates a string to the specified maximum length, appending an ellipsis if truncation occurs.

    Parameters:
        obj (str): The string to be truncated.
        max_length (int | None): The maximum allowed length of the string. If None, no truncation is performed.

    Returns:
        str: The original or truncated string, with an ellipsis appended if truncated.
    """
    if max_length is None or len(obj) <= max_length:
        return obj
    return obj[:max_length] + "..."


def _serialize_bytes(obj: bytes, max_length: int | None, _) -> str:
    """Decode bytes to string and truncate if max_length provided."""
    if max_length is not None:
        return (
            obj[:max_length].decode("utf-8", errors="ignore") + "..."
            if len(obj) > max_length
            else obj.decode("utf-8", errors="ignore")
        )
    return obj.decode("utf-8", errors="ignore")


def _serialize_datetime(obj: datetime, *_) -> str:
    """Convert datetime to UTC ISO format."""
    return obj.replace(tzinfo=timezone.utc).isoformat()


def _serialize_decimal(obj: Decimal, *_) -> float:
    """Convert Decimal to float."""
    return float(obj)


def _serialize_uuid(obj: UUID, *_) -> str:
    """Convert UUID to string."""
    return str(obj)


def _serialize_document(obj: Document, max_length: int | None, max_items: int | None, _seen: set[int] | None = None) -> Any:
    """Serialize Langchain Document recursively."""
    return serialize(obj.to_json(), max_length, max_items, _seen=_seen)


def _serialize_iterator(_: AsyncIterator | Generator | Iterator, *__) -> str:
    """Handle unconsumed iterators uniformly."""
    return "Unconsumed Stream"


def _serialize_sqlmodel(obj: Any, max_length: int | None, max_items: int | None, _seen: set[int] | None = None) -> Any:
    """Handle SQLModel instances, excluding relationships to prevent recursion."""
    if _seen is None:
        _seen = set()
    try:
        # SQLModel instances can have relationships that cause circular references
        # Use model_dump with mode='python' and exclude relationships
        if hasattr(obj, "model_dump"):
            # Try to get only the non-relationship fields
            # SQLModel relationships are typically not included in model_dump by default
            # but we'll be extra safe and exclude any relationship-like attributes
            try:
                # First, try model_dump with exclude to skip relationships
                # Get all field names that are relationships
                relationship_fields = set()
                if hasattr(obj, "__sqlmodel_relationships__"):
                    relationship_fields = set(obj.__sqlmodel_relationships__.keys())
                elif hasattr(obj, "__mapper__"):
                    # SQLAlchemy mapper approach
                    mapper = obj.__mapper__
                    relationship_fields = {rel.key for rel in mapper.relationships}
                
                # Use model_dump and filter out relationships
                serialized = obj.model_dump(mode="python")
                # Remove relationship fields to prevent recursion
                filtered = {k: v for k, v in serialized.items() if k not in relationship_fields}
                return {k: serialize(v, max_length, max_items, _seen=_seen) for k, v in filtered.items()}
            except Exception:
                # Fallback: just use model_dump and hope for the best
                serialized = obj.model_dump(mode="python")
                return {k: serialize(v, max_length, max_items, _seen=_seen) for k, v in serialized.items()}
        return str(obj)
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Cannot serialize SQLModel instance {obj}: {e!s}")
        return "[Unserializable SQLModel]"


def _serialize_pydantic(obj: BaseModel, max_length: int | None, max_items: int | None, _seen: set[int] | None = None) -> Any:
    """Handle modern Pydantic models."""
    if _seen is None:
        _seen = set()
    # Check if it's a SQLModel instance first (SQLModel is a subclass of BaseModel)
    if SQLModelType is not None and isinstance(obj, SQLModelType):
        return _serialize_sqlmodel(obj, max_length, max_items, _seen)
    serialized = obj.model_dump()
    return {k: serialize(v, max_length, max_items, _seen=_seen) for k, v in serialized.items()}


def _serialize_pydantic_v1(obj: BaseModelV1, max_length: int | None, max_items: int | None, _seen: set[int] | None = None) -> Any:
    """Backwards-compatible handling for Pydantic v1 models."""
    if _seen is None:
        _seen = set()
    if hasattr(obj, "to_json"):
        return serialize(obj.to_json(), max_length, max_items, _seen=_seen)
    return serialize(obj.dict(), max_length, max_items, _seen=_seen)


def _serialize_dict(obj: dict, max_length: int | None, max_items: int | None, _seen: set[int] | None = None) -> dict:
    """Recursively process dictionary values."""
    if _seen is None:
        _seen = set()
    return {k: serialize(v, max_length, max_items, _seen=_seen) for k, v in obj.items()}


def _serialize_list_tuple(obj: list | tuple, max_length: int | None, max_items: int | None, _seen: set[int] | None = None) -> list:
    """Truncate long lists and process items recursively."""
    if _seen is None:
        _seen = set()
    if max_items is not None and len(obj) > max_items:
        truncated = list(obj)[:max_items]
        truncated.append(f"... [truncated {len(obj) - max_items} items]")
        obj = truncated
    return [serialize(item, max_length, max_items, _seen=_seen) for item in obj]


def _serialize_primitive(obj: Any, *_) -> Any:
    """Handle primitive types without conversion."""
    if obj is None or isinstance(obj, int | float | bool | complex):
        return obj
    return UNSERIALIZABLE_SENTINEL


def _serialize_instance(obj: Any, *_) -> str:
    """Handle regular class instances by converting to string."""
    return str(obj)


def _truncate_value(value: Any, max_length: int | None, max_items: int | None) -> Any:
    """Truncate value based on its type and provided limits."""
    if max_length is not None and isinstance(value, str) and len(value) > max_length:
        return value[:max_length]
    if max_items is not None and isinstance(value, list | tuple) and len(value) > max_items:
        return value[:max_items]
    return value


def _serialize_dataframe(obj: pd.DataFrame, max_length: int | None, max_items: int | None) -> list[dict]:
    """Serialize pandas DataFrame to a dictionary format."""
    if max_items is not None and len(obj) > max_items:
        obj = obj.head(max_items)

    data = obj.to_dict(orient="records")

    return serialize(data, max_length, max_items)


def _serialize_series(obj: pd.Series, max_length: int | None, max_items: int | None) -> dict:
    """Serialize pandas Series to a dictionary format."""
    if max_items is not None and len(obj) > max_items:
        obj = obj.head(max_items)
    return {index: _truncate_value(value, max_length, max_items) for index, value in obj.items()}


def _is_numpy_type(obj: Any) -> bool:
    """Check if an object is a numpy type by checking its type's module name."""
    return hasattr(type(obj), "__module__") and type(obj).__module__ == np.__name__


def _serialize_numpy_type(obj: Any, max_length: int | None, max_items: int | None) -> Any:
    """Serialize numpy types."""
    try:
        # For single-element arrays
        if obj.size == 1 and hasattr(obj, "item"):
            return obj.item()

        # For multi-element arrays
        if np.issubdtype(obj.dtype, np.number):
            return obj.tolist()  # Convert to Python list
        if np.issubdtype(obj.dtype, np.bool_):
            return bool(obj)
        if np.issubdtype(obj.dtype, np.complexfloating):
            return complex(cast("complex", obj))
        if np.issubdtype(obj.dtype, np.str_):
            return _serialize_str(str(obj), max_length, max_items)
        if np.issubdtype(obj.dtype, np.bytes_) and hasattr(obj, "tobytes"):
            return _serialize_bytes(obj.tobytes(), max_length, max_items)
        if np.issubdtype(obj.dtype, np.object_) and hasattr(obj, "item"):
            return _serialize_instance(obj.item(), max_length, max_items)
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Cannot serialize numpy array: {e!s}")
        return UNSERIALIZABLE_SENTINEL
    return UNSERIALIZABLE_SENTINEL


def _serialize_dispatcher(obj: Any, max_length: int | None, max_items: int | None, _seen: set[int] | None = None) -> Any | _UnserializableSentinel:
    """Dispatch object to appropriate serializer."""
    if _seen is None:
        _seen = set()
    # Handle primitive types first
    if obj is None:
        return obj
    primitive = _serialize_primitive(obj, max_length, max_items)
    if primitive is not UNSERIALIZABLE_SENTINEL:
        return primitive

    match obj:
        case str():
            return _serialize_str(obj, max_length, max_items)
        case bytes():
            return _serialize_bytes(obj, max_length, max_items)
        case datetime():
            return _serialize_datetime(obj, max_length, max_items)
        case Decimal():
            return _serialize_decimal(obj, max_length, max_items)
        case UUID():
            return _serialize_uuid(obj, max_length, max_items)
        case Document():
            return _serialize_document(obj, max_length, max_items, _seen)
        case AsyncIterator() | Generator() | Iterator():
            return _serialize_iterator(obj, max_length, max_items)
        case BaseModel():
            return _serialize_pydantic(obj, max_length, max_items, _seen)
        case BaseModelV1():
            return _serialize_pydantic_v1(obj, max_length, max_items, _seen)
        case dict():
            return _serialize_dict(obj, max_length, max_items, _seen)
        case pd.DataFrame():
            return _serialize_dataframe(obj, max_length, max_items)
        case pd.Series():
            return _serialize_series(obj, max_length, max_items)
        case list() | tuple():
            return _serialize_list_tuple(obj, max_length, max_items, _seen)
        case object() if _is_numpy_type(obj):
            return _serialize_numpy_type(obj, max_length, max_items)
        case object() if not isinstance(obj, type):  # Match any instance that's not a class
            return _serialize_instance(obj, max_length, max_items)
        case object() if hasattr(obj, "_name_"):  # Enum case
            return f"{obj.__class__.__name__}.{obj._name_}"
        case object() if hasattr(obj, "__name__") and hasattr(obj, "__bound__"):  # TypeVar case
            return repr(obj)
        case object() if hasattr(obj, "__origin__") or hasattr(obj, "__parameters__"):  # Type alias/generic case
            return repr(obj)
        case _:
            # Handle numpy numeric types (int, float, bool, complex)
            if hasattr(obj, "dtype"):
                if np.issubdtype(obj.dtype, np.number) and hasattr(obj, "item"):
                    return obj.item()
                if np.issubdtype(obj.dtype, np.bool_):
                    return bool(obj)
                if np.issubdtype(obj.dtype, np.complexfloating):
                    return complex(cast("complex", obj))
                if np.issubdtype(obj.dtype, np.str_):
                    return str(obj)
                if np.issubdtype(obj.dtype, np.bytes_) and hasattr(obj, "tobytes"):
                    return obj.tobytes().decode("utf-8", errors="ignore")
                if np.issubdtype(obj.dtype, np.object_) and hasattr(obj, "item"):
                    return serialize(obj.item(), max_length, max_items, _seen=_seen)
            return UNSERIALIZABLE_SENTINEL


def serialize(
    obj: Any,
    max_length: int | None = None,
    max_items: int | None = None,
    *,
    to_str: bool = False,
    _seen: set[int] | None = None,
) -> Any:
    """Unified serialization with optional truncation support.

    Coordinates specialized serializers through a dispatcher pattern.
    Maintains recursive processing for nested structures.

    Args:
        obj: Object to serialize
        max_length: Maximum length for string values, None for no truncation
        max_items: Maximum items in list-like structures, None for no truncation
        to_str: If True, return a string representation of the object if serialization fails
        _seen: Internal parameter to track seen objects and prevent circular references
    """
    if obj is None:
        return None
    
    # Initialize seen set for recursion protection
    if _seen is None:
        _seen = set()
    
    # Only track mutable container types that can have circular references
    # Immutable types (str, int, float, tuple of immutables, etc.) don't need tracking
    is_trackable = isinstance(obj, (dict, list, set)) or (
        hasattr(obj, "__dict__") and not isinstance(obj, (str, bytes, int, float, bool, type))
    )
    
    obj_id = id(obj) if is_trackable else None
    
    # Check for circular references using object id
    if obj_id is not None and obj_id in _seen:
        # Circular reference detected - return a placeholder
        return "[Circular Reference]"
    
    # Add to seen set BEFORE processing to detect cycles
    if obj_id is not None:
        _seen.add(obj_id)
    
    try:
        # First try type-specific serialization
        result = _serialize_dispatcher(obj, max_length, max_items, _seen=_seen)
        if result is not UNSERIALIZABLE_SENTINEL:  # Special check for None since it's a valid result
            return result

        # Handle class-based Pydantic types and other types
        if isinstance(obj, type):
            if issubclass(obj, BaseModel | BaseModelV1):
                return repr(obj)
            return str(obj)  # Handle other class types

        # Handle type aliases and generic types
        if hasattr(obj, "__origin__") or hasattr(obj, "__parameters__"):  # Type alias or generic type check
            try:
                return repr(obj)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Cannot serialize object {obj}: {e!s}")

        # Check for SQLModel instances before general model_dump
        if SQLModelType is not None and isinstance(obj, SQLModelType):
            return _serialize_sqlmodel(obj, max_length, max_items, _seen)

        # Fallback to common serialization patterns
        if hasattr(obj, "model_dump"):
            return serialize(obj.model_dump(), max_length, max_items, _seen=_seen)
        if hasattr(obj, "dict") and not isinstance(obj, type):
            return serialize(obj.dict(), max_length, max_items, _seen=_seen)

        # Final fallback to string conversion only if explicitly requested
        if to_str:
            return str(obj)

        return obj

    except RecursionError:
        logger.warning(f"Recursion detected while serializing {type(obj).__name__}, returning placeholder")
        return "[Recursion Limit]"
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Cannot serialize object {obj}: {e!s}")
        return "[Unserializable Object]"
    finally:
        # Always remove from seen set when done processing this object
        if obj_id is not None:
            _seen.discard(obj_id)


def serialize_or_str(
    obj: Any,
    max_length: int | None = MAX_TEXT_LENGTH,
    max_items: int | None = MAX_ITEMS_LENGTH,
) -> Any:
    """Calls serialize() and if it fails, returns a string representation of the object.

    Args:
        obj: Object to serialize
        max_length: Maximum length for string values, None for no truncation
        max_items: Maximum items in list-like structures, None for no truncation
    """
    return serialize(obj, max_length, max_items, to_str=True)
