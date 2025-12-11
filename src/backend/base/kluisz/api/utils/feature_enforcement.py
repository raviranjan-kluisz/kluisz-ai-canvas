"""Feature enforcement utilities for API endpoints."""

from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status

from kluisz.api.utils import CurrentActiveUser
from kluisz.services.features.control_service import FeatureControlService


class FeatureNotEnabled(HTTPException):
    """Exception raised when a feature is not enabled for the user."""

    def __init__(self, feature_key: str, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail or f"Feature '{feature_key}' is not enabled for your license tier.",
        )


async def check_feature_enabled(
    feature_key: str,
    user: CurrentActiveUser,
    *,
    allow_superadmin: bool = True,
) -> bool:
    """
    Check if a feature is enabled for the current user.

    Args:
        feature_key: The feature key to check (e.g., "integrations.mcp")
        user: The current authenticated user
        allow_superadmin: If True, superadmins bypass feature checks

    Returns:
        True if the feature is enabled

    Raises:
        FeatureNotEnabled: If the feature is not enabled
    """
    # Superadmins bypass all feature checks
    if allow_superadmin and user.is_platform_superadmin:
        return True

    service = FeatureControlService()
    is_enabled = await service.is_feature_enabled(str(user.id), feature_key)

    if not is_enabled:
        raise FeatureNotEnabled(feature_key)

    return True


def require_feature(
    feature_key: str,
    *,
    allow_superadmin: bool = True,
    detail: str | None = None,
) -> Callable:
    """
    Dependency that requires a specific feature to be enabled.

    Usage:
        @router.post("/mcp/servers")
        async def create_mcp_server(
            ...,
            _: bool = Depends(require_feature("integrations.mcp")),
        ):
            ...

    Args:
        feature_key: The feature key to check
        allow_superadmin: If True, superadmins bypass feature checks
        detail: Custom error message

    Returns:
        A FastAPI dependency function
    """

    async def dependency(user: CurrentActiveUser) -> bool:
        # Superadmins bypass all feature checks
        if allow_superadmin and user.is_platform_superadmin:
            return True

        service = FeatureControlService()
        is_enabled = await service.is_feature_enabled(str(user.id), feature_key)

        if not is_enabled:
            raise FeatureNotEnabled(feature_key, detail)

        return True

    return dependency


def require_any_feature(
    *feature_keys: str,
    allow_superadmin: bool = True,
    detail: str | None = None,
) -> Callable:
    """
    Dependency that requires ANY of the specified features to be enabled.

    Usage:
        @router.post("/api/something")
        async def do_something(
            ...,
            _: bool = Depends(require_any_feature("feature.a", "feature.b")),
        ):
            ...

    Args:
        feature_keys: The feature keys to check (at least one must be enabled)
        allow_superadmin: If True, superadmins bypass feature checks
        detail: Custom error message

    Returns:
        A FastAPI dependency function
    """

    async def dependency(user: CurrentActiveUser) -> bool:
        # Superadmins bypass all feature checks
        if allow_superadmin and user.is_platform_superadmin:
            return True

        service = FeatureControlService()

        for feature_key in feature_keys:
            is_enabled = await service.is_feature_enabled(str(user.id), feature_key)
            if is_enabled:
                return True

        raise FeatureNotEnabled(
            ", ".join(feature_keys),
            detail or f"At least one of these features must be enabled: {', '.join(feature_keys)}",
        )

    return dependency


def require_all_features(
    *feature_keys: str,
    allow_superadmin: bool = True,
    detail: str | None = None,
) -> Callable:
    """
    Dependency that requires ALL specified features to be enabled.

    Usage:
        @router.post("/api/something")
        async def do_something(
            ...,
            _: bool = Depends(require_all_features("feature.a", "feature.b")),
        ):
            ...

    Args:
        feature_keys: The feature keys to check (all must be enabled)
        allow_superadmin: If True, superadmins bypass feature checks
        detail: Custom error message

    Returns:
        A FastAPI dependency function
    """

    async def dependency(user: CurrentActiveUser) -> bool:
        # Superadmins bypass all feature checks
        if allow_superadmin and user.is_platform_superadmin:
            return True

        service = FeatureControlService()
        missing_features = []

        for feature_key in feature_keys:
            is_enabled = await service.is_feature_enabled(str(user.id), feature_key)
            if not is_enabled:
                missing_features.append(feature_key)

        if missing_features:
            raise FeatureNotEnabled(
                ", ".join(missing_features),
                detail or f"These features must be enabled: {', '.join(missing_features)}",
            )

        return True

    return dependency


