# Feature Control Service - Backend Implementation

## 1. Service Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    FeatureControlService                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ FeatureRegistry  │  │ TierFeature      │                  │
│  │    Manager       │  │    Manager       │                  │
│  └────────┬─────────┘  └────────┬─────────┘                  │
│           │                     │                    │         │
│           └─────────────────────┼────────────────────┘         │
│                                 │                              │
│                    ┌────────────▼────────────┐                 │
│                    │   FeatureResolver       │                 │
│                    │   (Cascade Logic)       │                 │
│                    └────────────┬────────────┘                 │
│                                 │                              │
│                    ┌────────────▼────────────┐                 │
│                    │   FeatureCache          │                 │
│                    │   (Redis/Memory)        │                 │
│                    └─────────────────────────┘                 │
└────────────────────────────────────────────────────────────────┘
```

## 2. Core Service Implementation

### 2.1 Feature Control Service

**Location:** `src/backend/base/kluisz/services/features/control_service.py`

```python
"""Feature Control Service - Manages tenant feature flags and overrides."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, TypedDict
from uuid import UUID

from klx.log.logger import logger
from klx.services.deps import session_scope
from sqlmodel import select, and_

from kluisz.schema.serialize import UUIDstr, str_to_uuid
from kluisz.services.base import Service
from kluisz.services.cache import get_cache_service


class FeatureValue(TypedDict, total=False):
    """Type for feature values."""
    enabled: bool
    value: Any
    source: str  # 'default', 'tier'
    expires_at: str | None


class ResolvedFeatures(TypedDict):
    """Resolved features for a tenant."""
    features: dict[str, FeatureValue]
    tier_id: str | None
    tier_name: str | None
    computed_at: str
    cache_key: str


class FeatureControlService(Service):
    """
    Manages feature flags with simple inheritance:
    Global Registry -> License Tier -> Tenant (via tier)
    
    Features:
    - Fast resolution with caching
    - Audit logging for all changes
    - Dependency checking
    - Simple model: tenants inherit features from their assigned tier
    """

    name = "feature_control_service"
    CACHE_TTL = 300  # 5 minutes
    CACHE_PREFIX = "features:"

    @property
    def ready(self) -> bool:
        return True

    # =========================================================================
    # FEATURE RESOLUTION (Core Logic)
    # =========================================================================

    async def get_user_features(
        self,
        user_id: UUIDstr,
        *,
        bypass_cache: bool = False,
    ) -> ResolvedFeatures:
        """
        Get all resolved features for a user.
        
        Resolution order:
        1. Check cache (unless bypass_cache=True)
        2. Get user's license tier (from user.license_tier_id)
        3. Get tier's feature definitions
        4. Check feature dependencies
        5. Cache and return
        
        Args:
            user_id: User UUID
            bypass_cache: Skip cache lookup
            
        Returns:
            ResolvedFeatures with all feature values and metadata
        """
        cache_key = f"{self.CACHE_PREFIX}user:{user_id}"
        
        # Check cache first
        if not bypass_cache:
            cached = await self._get_cached_features(cache_key)
            if cached:
                return cached
        
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.license_tier.model import LicenseTier
        
        async with session_scope() as session:
            # Get user with tier
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Start with global defaults
            features = await self._get_global_defaults(session)
            tier_id = None
            tier_name = None
            
            # Apply tier features if user has a license tier assigned
            if user.license_tier_id:
                tier = await session.get(LicenseTier, user.license_tier_id)
                if tier:
                    tier_id = str(tier.id)
                    tier_name = tier.name
                    features = await self._apply_tier_features(
                        session, features, tier.id
                    )
            
            # Resolve dependencies
            features = self._resolve_dependencies(features)
            
            # Build response
            result: ResolvedFeatures = {
                "features": features,
                "tier_id": tier_id,
                "tier_name": tier_name,
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "cache_key": cache_key,
            }
            
            # Cache result
            await self._cache_features(cache_key, result)
            
            return result

    async def is_feature_enabled(
        self,
        user_id: UUIDstr,
        feature_key: str,
    ) -> bool:
        """
        Quick check if a specific feature is enabled for a user.
        
        Args:
            user_id: User UUID
            feature_key: Feature key (e.g., "models.openai")
            
        Returns:
            True if feature is enabled
        """
        features = await self.get_user_features(user_id)
        feature = features["features"].get(feature_key)
        
        if not feature:
            return False
            
        # Check expiration
        if feature.get("expires_at"):
            expires = datetime.fromisoformat(feature["expires_at"])
            if expires < datetime.now(timezone.utc):
                return False
        
        return feature.get("enabled", False)

    async def get_enabled_models(
        self,
        user_id: UUIDstr,
    ) -> list[dict[str, Any]]:
        """
        Get list of enabled models for a user.
        
        Returns:
            List of enabled models with metadata
        """
        features = await self.get_user_features(user_id)
        
        # Import model registry
        from kluisz.services.database.models.feature.model import ModelRegistry
        
        enabled_models = []
        
        async with session_scope() as session:
            # Get all models
            stmt = select(ModelRegistry).where(ModelRegistry.is_active == True)
            result = await session.exec(stmt)
            models = list(result.all())
            
            for model in models:
                # Check if model's feature is enabled
                feature = features["features"].get(model.feature_key)
                if feature and feature.get("enabled"):
                    enabled_models.append({
                        "provider": model.provider,
                        "model_id": model.model_id,
                        "model_name": model.model_name,
                        "model_type": model.model_type,
                        "supports_tools": model.supports_tools,
                        "supports_vision": model.supports_vision,
                        "max_tokens": model.max_tokens,
                    })
        
        return enabled_models

    async def get_enabled_components(
        self,
        user_id: UUIDstr,
    ) -> list[str]:
        """
        Get list of enabled component keys for a user.
        
        Returns:
            List of enabled component keys
        """
        features = await self.get_user_features(user_id)
        
        from kluisz.services.database.models.feature.model import ComponentRegistry
        
        enabled_components = []
        
        async with session_scope() as session:
            stmt = select(ComponentRegistry).where(ComponentRegistry.is_active == True)
            result = await session.exec(stmt)
            components = list(result.all())
            
            for comp in components:
                # Check component's feature
                if comp.feature_key:
                    feature = features["features"].get(comp.feature_key)
                    if not feature or not feature.get("enabled"):
                        continue
                
                # Check required features
                if comp.required_features:
                    all_required = all(
                        features["features"].get(f, {}).get("enabled", False)
                        for f in comp.required_features
                    )
                    if not all_required:
                        continue
                
                enabled_components.append(comp.component_key)
        
        return enabled_components

    # =========================================================================
    # TIER FEATURE MANAGEMENT (Super Admin)
    # =========================================================================

    async def set_tier_features(
        self,
        tier_id: UUIDstr,
        features: dict[str, Any],
        *,
        updated_by: UUIDstr,
    ) -> None:
        """
        Set features for a license tier.
        
        Args:
            tier_id: License tier UUID
            features: Feature key -> value mapping
            updated_by: Super admin user ID
        """
        from kluisz.services.database.models.feature.model import (
            LicenseTierFeatures,
            FeatureRegistry,
        )
        
        async with session_scope() as session:
            for feature_key, value in features.items():
                # Validate feature exists
                registry_stmt = select(FeatureRegistry).where(
                    FeatureRegistry.feature_key == feature_key
                )
                result = await session.exec(registry_stmt)
                registry_entry = result.first()
                
                if not registry_entry:
                    logger.warning(f"Unknown feature key: {feature_key}")
                    continue
                
                # Upsert tier feature
                stmt = select(LicenseTierFeatures).where(
                    and_(
                        LicenseTierFeatures.license_tier_id == str_to_uuid(tier_id),
                        LicenseTierFeatures.feature_key == feature_key,
                    )
                )
                result = await session.exec(stmt)
                tier_feature = result.first()
                
                feature_value = self._normalize_feature_value(value)
                
                if tier_feature:
                    tier_feature.feature_value = feature_value
                    tier_feature.updated_at = datetime.now(timezone.utc)
                else:
                    tier_feature = LicenseTierFeatures(
                        license_tier_id=str_to_uuid(tier_id),
                        feature_key=feature_key,
                        feature_value=feature_value,
                        created_by=str_to_uuid(updated_by),
                    )
                    session.add(tier_feature)
                
                # Audit log
                await self._log_feature_change(
                    session,
                    entity_type="tier",
                    entity_id=tier_id,
                    feature_key=feature_key,
                    action="update",
                    new_value=feature_value,
                    performed_by=updated_by,
                )
            
            await session.commit()
        
        # Invalidate cache for all users with this tier
        await self._invalidate_tier_cache(tier_id)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _get_global_defaults(
        self,
        session,
    ) -> dict[str, FeatureValue]:
        """Get all features with their global defaults."""
        from kluisz.services.database.models.feature.model import FeatureRegistry
        
        stmt = select(FeatureRegistry).where(FeatureRegistry.is_active == True)
        result = await session.exec(stmt)
        features = {}
        
        for reg in result.all():
            features[reg.feature_key] = {
                "enabled": reg.default_value.get("enabled", False) if isinstance(reg.default_value, dict) else bool(reg.default_value),
                "value": reg.default_value,
                "source": "default",
                "expires_at": None,
            }
        
        return features

    async def _apply_tier_features(
        self,
        session,
        features: dict[str, FeatureValue],
        tier_id: UUID,
    ) -> dict[str, FeatureValue]:
        """Apply license tier feature definitions."""
        from kluisz.services.database.models.feature.model import LicenseTierFeatures
        
        stmt = select(LicenseTierFeatures).where(
            LicenseTierFeatures.license_tier_id == tier_id
        )
        result = await session.exec(stmt)
        
        for tier_feature in result.all():
            value = tier_feature.feature_value
            features[tier_feature.feature_key] = {
                "enabled": value.get("enabled", False) if isinstance(value, dict) else bool(value),
                "value": value,
                "source": "tier",
                "expires_at": None,
            }
        
        return features

    def _resolve_dependencies(
        self,
        features: dict[str, FeatureValue],
    ) -> dict[str, FeatureValue]:
        """
        Resolve feature dependencies.
        If a feature is enabled but its dependencies are not, disable it.
        """
        # TODO: Implement dependency resolution from feature_registry.depends_on
        # For now, return as-is
        return features

    def _normalize_feature_value(self, value: Any) -> dict:
        """Normalize feature value to standard format."""
        if isinstance(value, bool):
            return {"enabled": value}
        if isinstance(value, dict):
            return value
        return {"enabled": bool(value), "value": value}

    async def _get_cached_features(self, cache_key: str) -> ResolvedFeatures | None:
        """Get features from cache."""
        try:
            cache = get_cache_service()
            cached = await cache.get(cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    async def _cache_features(self, cache_key: str, features: ResolvedFeatures) -> None:
        """Cache resolved features."""
        try:
            cache = get_cache_service()
            await cache.set(cache_key, features, ttl=self.CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def _invalidate_user_cache(self, user_id: UUIDstr) -> None:
        """Invalidate cache for a specific user."""
        cache_key = f"{self.CACHE_PREFIX}user:{user_id}"
        try:
            cache = get_cache_service()
            await cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")

    async def _invalidate_tier_cache(self, tier_id: UUIDstr) -> None:
        """Invalidate cache for all users with this tier."""
        from kluisz.services.database.models.user.model import User
        
        async with session_scope() as session:
            user_stmt = select(User.id).where(User.license_tier_id == str_to_uuid(tier_id))
            user_result = await session.exec(user_stmt)
            for (user_id,) in user_result.all():
                await self._invalidate_user_cache(str(user_id))

    async def _log_feature_change(
        self,
        session,
        *,
        entity_type: str,
        entity_id: str,
        feature_key: str,
        action: str,
        new_value: Any = None,
        old_value: Any = None,
        performed_by: str,
        reason: str | None = None,
    ) -> None:
        """Log feature changes for audit."""
        from kluisz.services.database.models.feature.model import FeatureAuditLog
        
        log = FeatureAuditLog(
            entity_type=entity_type,
            entity_id=str_to_uuid(entity_id),
            feature_key=feature_key,
            action=action,
            old_value=old_value,
            new_value=new_value,
            performed_by=str_to_uuid(performed_by),
            reason=reason,
        )
        session.add(log)

    async def teardown(self) -> None:
        """Cleanup resources."""
        pass
```

## 3. API Endpoints

### 3.1 Feature Resolution API

**Location:** `src/backend/base/kluisz/api/v2/features.py`

```python
"""Feature API endpoints for users."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from kluisz.services.auth.utils import CurrentUser, get_current_user
from kluisz.services.features.control_service import FeatureControlService

router = APIRouter(prefix="/features", tags=["Features"])


class FeatureResponse(BaseModel):
    features: dict
    tier_name: str | None
    computed_at: str


class FeatureCheckResponse(BaseModel):
    feature_key: str
    enabled: bool
    source: str


@router.get("", response_model=FeatureResponse)
async def get_my_features(
    current_user: CurrentUser,
) -> FeatureResponse:
    """Get all enabled features for current user."""
    service = FeatureControlService()
    result = await service.get_user_features(str(current_user.id))
    
    return FeatureResponse(
        features=result["features"],
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


@router.get("/models")
async def get_available_models(
    current_user: CurrentUser,
):
    """Get list of available models for current user."""
    service = FeatureControlService()
    return await service.get_enabled_models(str(current_user.id))


@router.get("/components")
async def get_available_components(
    current_user: CurrentUser,
):
    """Get list of available component keys for current user."""
    service = FeatureControlService()
    return await service.get_enabled_components(str(current_user.id))
```

### 3.2 Admin Feature Management API

**Location:** `src/backend/base/kluisz/api/v2/admin/features.py`

```python
"""Admin API endpoints for feature management."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from kluisz.services.auth.utils import SuperAdmin, TenantAdminOrSuperAdmin
from kluisz.services.features.control_service import FeatureControlService

router = APIRouter(prefix="/admin/features", tags=["Admin - Features"])


class SetTierFeaturesRequest(BaseModel):
    features: dict[str, bool | dict]


class SetTenantOverrideRequest(BaseModel):
    feature_key: str
    value: bool | dict
    valid_until: datetime | None = None
    reason: str | None = None


class ApproveUpgradeRequest(BaseModel):
    valid_until: datetime | None = None
    notes: str | None = None


# =========================================================================
# TIER FEATURE MANAGEMENT (Super Admin Only)
# =========================================================================

@router.put("/tiers/{tier_id}")
async def set_tier_features(
    tier_id: str,
    request: SetTierFeaturesRequest,
    current_user: SuperAdmin,
):
    """Set features for a license tier."""
    service = FeatureControlService()
    await service.set_tier_features(
        tier_id=tier_id,
        features=request.features,
        updated_by=str(current_user.id),
    )
    return {"status": "ok", "updated_features": len(request.features)}


@router.get("/tiers/{tier_id}")
async def get_tier_features(
    tier_id: str,
    current_user: SuperAdmin,
):
    """Get all features defined for a tier."""
    from klx.services.deps import session_scope
    from sqlmodel import select
    from kluisz.services.database.models.feature.model import LicenseTierFeatures
    from kluisz.schema.serialize import str_to_uuid
    
    async with session_scope() as session:
        stmt = select(LicenseTierFeatures).where(
            LicenseTierFeatures.license_tier_id == str_to_uuid(tier_id)
        )
        result = await session.exec(stmt)
        features = {f.feature_key: f.feature_value for f in result.all()}
    
    return {"tier_id": tier_id, "features": features}


# =========================================================================
# FEATURE REGISTRY MANAGEMENT
# =========================================================================

@router.get("/registry")
async def list_feature_registry(
    current_user: SuperAdmin,
    category: str | None = None,
):
    """List all features in the registry."""
    from klx.services.deps import session_scope
    from sqlmodel import select
    from kluisz.services.database.models.feature.model import FeatureRegistry
    
    async with session_scope() as session:
        stmt = select(FeatureRegistry)
        if category:
            stmt = stmt.where(FeatureRegistry.category == category)
        stmt = stmt.order_by(FeatureRegistry.category, FeatureRegistry.display_order)
        
        result = await session.exec(stmt)
        features = [
            {
                "feature_key": f.feature_key,
                "feature_name": f.feature_name,
                "description": f.description,
                "category": f.category,
                "subcategory": f.subcategory,
                "feature_type": f.feature_type,
                "default_value": f.default_value,
                "is_premium": f.is_premium,
                "is_active": f.is_active,
            }
            for f in result.all()
        ]
    
    return {"features": features}
```

## 4. Database Models

**Location:** `src/backend/base/kluisz/services/database/models/feature/model.py`

See ERD in architecture.md for complete model definitions.




