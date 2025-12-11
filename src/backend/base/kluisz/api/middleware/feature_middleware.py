"""
Feature Enforcement Middleware - Automatic route protection.

This middleware automatically enforces feature requirements based on
route patterns defined in route_features.py.

No endpoint decoration needed - just add routes to ROUTE_FEATURE_MAP.

@see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md - Pattern 2
"""

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from klx.log.logger import logger
from starlette.middleware.base import BaseHTTPMiddleware

from kluisz.api.middleware.route_features import get_required_features, is_route_exempt
from kluisz.services.features.control_service import FeatureControlService


class FeatureEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically enforces feature requirements based on route patterns.

    This eliminates the need to decorate each endpoint individually.
    Protection is configured centrally in route_features.py.

    Behavior:
    - Exempt routes bypass all checks
    - Unauthenticated requests pass through (auth middleware handles that)
    - Superadmins bypass feature checks
    - Regular users need at least ONE required feature enabled (OR logic)

    Usage:
        app.add_middleware(FeatureEnforcementMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip exempt routes
        if is_route_exempt(path):
            return await call_next(request)

        # Get required features for this route
        required_features = get_required_features(path)

        if not required_features:
            # No specific requirements, allow
            return await call_next(request)

        # Get current user from request state
        # (set by auth middleware earlier in the chain)
        user = getattr(request.state, "user", None)

        if not user:
            # Not authenticated - let auth middleware handle it
            # Or they're accessing a route that doesn't require auth
            return await call_next(request)

        # Superadmins bypass all feature checks
        if getattr(user, "is_platform_superadmin", False):
            return await call_next(request)

        # Check features (OR logic - any enabled feature allows access)
        try:
            service = FeatureControlService()
            user_id = str(user.id) if hasattr(user, "id") else str(user)

            for feature_key in required_features:
                try:
                    if await service.is_feature_enabled(user_id, feature_key):
                        # At least one required feature is enabled
                        return await call_next(request)
                except Exception as e:
                    # Log but don't fail on feature check errors
                    await logger.awarning(
                        f"Feature check error for {feature_key}: {e}"
                    )
                    continue

        except Exception as e:
            # If feature service fails, log and allow (fail-open for service errors)
            # This prevents total lockout if the feature service is down
            await logger.aerror(f"Feature middleware error: {e}")
            return await call_next(request)

        # No required features are enabled - deny access
        return JSONResponse(
            status_code=403,
            content={
                "detail": "This feature is not available in your current plan.",
                "error_code": "FEATURE_NOT_ENABLED",
                "required_features": required_features,
                "message": f"Access requires one of: {', '.join(required_features)}",
                "upgrade_url": "/settings/subscription",
            },
        )


class FeatureEnforcementMiddlewareStrict(BaseHTTPMiddleware):
    """
    Strict version of feature enforcement middleware.

    Same as FeatureEnforcementMiddleware but fails-closed on errors.
    Use this in high-security environments where feature bypass is unacceptable.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if is_route_exempt(path):
            return await call_next(request)

        required_features = get_required_features(path)

        if not required_features:
            return await call_next(request)

        user = getattr(request.state, "user", None)

        if not user:
            return await call_next(request)

        if getattr(user, "is_platform_superadmin", False):
            return await call_next(request)

        # Strict mode: fail-closed on ANY error
        try:
            service = FeatureControlService()
            user_id = str(user.id) if hasattr(user, "id") else str(user)

            for feature_key in required_features:
                if await service.is_feature_enabled(user_id, feature_key):
                    return await call_next(request)

        except Exception as e:
            # Fail-closed: deny on error
            await logger.aerror(f"Feature middleware error (strict mode): {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Feature verification service unavailable.",
                    "error_code": "FEATURE_SERVICE_ERROR",
                },
            )

        return JSONResponse(
            status_code=403,
            content={
                "detail": "This feature is not available in your current plan.",
                "error_code": "FEATURE_NOT_ENABLED",
                "required_features": required_features,
                "message": f"Access requires one of: {', '.join(required_features)}",
                "upgrade_url": "/settings/subscription",
            },
        )


