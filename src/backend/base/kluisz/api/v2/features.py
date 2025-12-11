"""Feature API endpoints for users."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from kluisz.api.utils import CurrentActiveUser
from kluisz.services.auth.utils import get_current_active_superuser
from kluisz.services.database.models.user.model import User
from kluisz.services.features.control_service import FeatureControlService
from kluisz.services.limits.enforcement import get_limits_enforcement_service

# Type aliases for dependencies
CurrentUser = CurrentActiveUser
SuperAdmin = Annotated[User, Depends(get_current_active_superuser)]

router = APIRouter(prefix="/features", tags=["Features"])


# ============================================
# Response Models
# ============================================


class FeatureResponse(BaseModel):
    """Response model for user features."""

    features: dict[str, Any]
    tier_id: str | None
    tier_name: str | None
    computed_at: str


class FeatureCheckResponse(BaseModel):
    """Response model for feature check."""

    feature_key: str
    enabled: bool
    source: str


class EnabledModel(BaseModel):
    """Response model for enabled model."""

    provider: str
    model_id: str
    model_name: str
    model_type: str
    supports_tools: bool
    supports_vision: bool
    max_tokens: int | None


# ============================================
# User Feature Endpoints
# ============================================


@router.get("", response_model=FeatureResponse)
async def get_my_features(
    current_user: CurrentUser,
) -> FeatureResponse:
    """Get all enabled features for current user."""
    service = FeatureControlService()
    result = await service.get_user_features(str(current_user.id))

    return FeatureResponse(
        features=result["features"],
        tier_id=result["tier_id"],
        tier_name=result["tier_name"],
        computed_at=result["computed_at"],
    )


@router.get("/check/{feature_key}")
async def check_feature(
    feature_key: str,
    current_user: CurrentUser,
) -> FeatureCheckResponse:
    """Check if a specific feature is enabled for current user."""
    service = FeatureControlService()
    result = await service.get_user_features(str(current_user.id))

    feature = result["features"].get(feature_key)

    return FeatureCheckResponse(
        feature_key=feature_key,
        enabled=feature.get("enabled", False) if feature else False,
        source=feature.get("source", "not_found") if feature else "not_found",
    )


@router.get("/models", response_model=list[EnabledModel])
async def get_available_models(
    current_user: CurrentUser,
) -> list[EnabledModel]:
    """Get list of available models for current user."""
    service = FeatureControlService()
    models = await service.get_enabled_models(str(current_user.id))
    return [EnabledModel(**m) for m in models]


@router.get("/components")
async def get_available_components(
    current_user: CurrentUser,
) -> list[str]:
    """Get list of available component keys for current user."""
    service = FeatureControlService()
    return await service.get_enabled_components(str(current_user.id))


class LimitsResponse(BaseModel):
    """Response model for user limits."""

    user_id: str
    is_superadmin: bool
    message: str | None = None
    flows: dict[str, Any] | None = None
    api_calls: dict[str, Any] | None = None
    tier: dict[str, str] | None = None


@router.get("/limits", response_model=LimitsResponse)
async def get_my_limits(
    current_user: CurrentUser,
) -> LimitsResponse:
    """Get resource limits and usage for current user.
    
    Returns:
        - flows: Current flow count, max allowed, remaining
        - api_calls: Current API calls this billing period, max allowed, remaining
        - tier: User's license tier info
    """
    service = get_limits_enforcement_service()
    result = await service.get_user_limits_status(str(current_user.id))
    return LimitsResponse(**result)


# ============================================
# Admin Feature Endpoints
# ============================================


class SetTierFeaturesRequest(BaseModel):
    """Request model for setting tier features."""

    features: dict[str, bool | dict[str, Any]]


class TierFeaturesResponse(BaseModel):
    """Response model for tier features."""

    tier_id: str
    features: dict[str, Any]


class FeatureRegistryItem(BaseModel):
    """Response model for feature registry item."""

    feature_key: str
    feature_name: str
    description: str | None
    category: str
    subcategory: str | None
    feature_type: str
    default_value: dict[str, Any]
    is_premium: bool
    is_active: bool


@router.put("/admin/tiers/{tier_id}")
async def set_tier_features(
    tier_id: str,
    request: SetTierFeaturesRequest,
    current_user: SuperAdmin,
) -> dict[str, Any]:
    """Set features for a license tier. Super Admin only."""
    service = FeatureControlService()
    await service.set_tier_features(
        tier_id=tier_id,
        features=request.features,
        updated_by=str(current_user.id),
    )
    return {"status": "ok", "updated_features": len(request.features)}


@router.get("/admin/tiers/{tier_id}", response_model=TierFeaturesResponse)
async def get_tier_features(
    tier_id: str,
    current_user: SuperAdmin,
) -> TierFeaturesResponse:
    """Get all features defined for a tier. Super Admin only."""
    service = FeatureControlService()
    features = await service.get_tier_features(tier_id)
    return TierFeaturesResponse(tier_id=tier_id, features=features)


@router.get("/admin/registry", response_model=list[FeatureRegistryItem])
async def list_feature_registry(
    current_user: SuperAdmin,
    category: str | None = None,
) -> list[FeatureRegistryItem]:
    """List all features in the registry. Super Admin only."""
    service = FeatureControlService()
    features = await service.get_feature_registry(category=category)
    return [FeatureRegistryItem(**f) for f in features]

