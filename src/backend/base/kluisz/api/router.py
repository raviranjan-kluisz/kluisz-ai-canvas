# Router for base api
from fastapi import APIRouter

from kluisz.api.v1 import (
    api_key_router,
    billing_router,
    chat_router,
    endpoints_router,
    files_router,
    flows_router,
    folders_router,
    knowledge_bases_router,
    licenses_router,
    login_router,
    mcp_projects_router,
    mcp_router,
    monitor_router,
    openai_responses_router,
    projects_router,
    starter_projects_router,
    store_router,
    tenants_router,
    users_router,
    validate_router,
    variables_router,
)
from kluisz.api.v1.voice_mode import router as voice_mode_router
from kluisz.api.v2 import (
    analytics_router as analytics_router_v2,
    features_router as features_router_v2,
    files_router as files_router_v2,
    license_pools_router as license_pools_router_v2,
    license_tiers_router as license_tiers_router_v2,
    mcp_router as mcp_router_v2,
    registration_router as registration_router_v2,
    user_licenses_router as user_licenses_router_v2,
)

router_v1 = APIRouter(
    prefix="/v1",
)

router_v2 = APIRouter(
    prefix="/v2",
)

router_v1.include_router(chat_router)
router_v1.include_router(endpoints_router)
router_v1.include_router(validate_router)
router_v1.include_router(store_router)
router_v1.include_router(flows_router)
router_v1.include_router(users_router)
router_v1.include_router(api_key_router)
router_v1.include_router(login_router)
router_v1.include_router(variables_router)
router_v1.include_router(files_router)
router_v1.include_router(monitor_router)
router_v1.include_router(folders_router)
router_v1.include_router(projects_router)
router_v1.include_router(starter_projects_router)
router_v1.include_router(knowledge_bases_router)
router_v1.include_router(mcp_router)
router_v1.include_router(voice_mode_router)
router_v1.include_router(mcp_projects_router)
router_v1.include_router(openai_responses_router)
# Multi-tenant management
router_v1.include_router(tenants_router)
router_v1.include_router(licenses_router)
router_v1.include_router(billing_router)

router_v2.include_router(files_router_v2)
router_v2.include_router(features_router_v2)
router_v2.include_router(mcp_router_v2)
router_v2.include_router(registration_router_v2)
router_v2.include_router(license_tiers_router_v2)
router_v2.include_router(license_pools_router_v2)
router_v2.include_router(user_licenses_router_v2)
router_v2.include_router(analytics_router_v2)

router = APIRouter(
    prefix="/api",
)
router.include_router(router_v1)
router.include_router(router_v2)
