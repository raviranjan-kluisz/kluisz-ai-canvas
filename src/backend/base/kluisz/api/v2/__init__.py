from kluisz.api.v2.analytics import router as analytics_router
from kluisz.api.v2.features import router as features_router
from kluisz.api.v2.files import router as files_router
from kluisz.api.v2.license_pools import router as license_pools_router
from kluisz.api.v2.license_tiers import router as license_tiers_router
from kluisz.api.v2.mcp import router as mcp_router
from kluisz.api.v2.registration import router as registration_router
from kluisz.api.v2.user_licenses import router as user_licenses_router

__all__ = [
    "analytics_router",
    "features_router",
    "files_router",
    "license_pools_router",
    "license_tiers_router",
    "mcp_router",
    "registration_router",
    "user_licenses_router",
]
