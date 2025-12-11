"""
Route Feature Configuration - Central mapping of routes to required features.

This is the SINGLE SOURCE OF TRUTH for backend route protection.
To protect a new route, add it to ROUTE_FEATURE_MAP.
No endpoint code changes needed.

@see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md - Pattern 2
"""

import re
from typing import Dict, List


# =============================================================================
# ROUTE FEATURE MAPPINGS
# =============================================================================

# Central configuration: route patterns → required features (OR logic)
# If ANY feature in the list is enabled, access is granted.
ROUTE_FEATURE_MAP: Dict[str, List[str]] = {
    # =========================================================================
    # MCP ENDPOINTS
    # =========================================================================
    r"^/api/v[12]/mcp/servers.*": [
        "integrations.mcp",
        "ui.advanced.mcp_server_config",
    ],
    r"^/api/v[12]/mcp/sse.*": [
        "integrations.mcp",
    ],
    
    # =========================================================================
    # CUSTOM COMPONENTS
    # =========================================================================
    r"^/api/v[12]/custom-components.*": [
        "components.custom.enabled",
    ],
    r"^/api/v[12]/components/.*/code$": [
        "components.custom.code_editing",
        "ui.code_view.edit_code",
    ],
    r"^/api/v[12]/validate/code.*": [
        "components.custom.code_editing",
        "ui.code_view.edit_code",
    ],
    
    # =========================================================================
    # FLOW OPERATIONS
    # =========================================================================
    r"^/api/v[12]/flows/.*/export$": [
        "ui.flow_builder.export_flow",
    ],
    r"^/api/v[12]/flows/.*/import$": [
        "ui.flow_builder.import_flow",
    ],
    r"^/api/v[12]/flows/.*/share$": [
        "ui.flow_builder.share_flow",
    ],
    r"^/api/v[12]/flows/.*/versions.*": [
        "ui.flow_builder.version_control",
    ],
    r"^/api/v[12]/flows/.*/duplicate$": [
        "ui.flow_builder.duplicate_flow",
    ],
    
    # =========================================================================
    # API ACCESS
    # =========================================================================
    r"^/api/v[12]/api[_-]?keys.*": [
        "ui.advanced.api_keys_management",
    ],
    r"^/api/v[12]/webhooks.*": [
        "api.webhooks",
    ],
    r"^/api/v[12]/batch.*": [
        "api.batch_execution",
    ],
    
    # =========================================================================
    # GLOBAL VARIABLES
    # =========================================================================
    r"^/api/v[12]/variables.*": [
        "ui.advanced.global_variables",
    ],
    
    # =========================================================================
    # INTEGRATIONS - OBSERVABILITY
    # NOTE: All observability (Langfuse, LangSmith, LangWatch) is mandatory/always-on
    # These are used for system logging - no feature gate needed
    # =========================================================================
    
    # =========================================================================
    # INTEGRATIONS - VECTOR STORES
    # =========================================================================
    r"^/api/v[12]/vector[_-]?stores/pinecone.*": [
        "integrations.vector_stores.pinecone",
    ],
    r"^/api/v[12]/vector[_-]?stores/qdrant.*": [
        "integrations.vector_stores.qdrant",
    ],
    r"^/api/v[12]/vector[_-]?stores/weaviate.*": [
        "integrations.vector_stores.weaviate",
    ],
    r"^/api/v[12]/vector[_-]?stores/milvus.*": [
        "integrations.vector_stores.milvus",
    ],
    
    # =========================================================================
    # STORE (External Components)
    # =========================================================================
    r"^/api/v[12]/store/components/download.*": [
        "components.custom.import_external",
    ],
    r"^/api/v[12]/store/components/upload.*": [
        "ui.flow_builder.share_flow",
    ],
}


# =============================================================================
# EXEMPT ROUTES (bypass feature checks)
# =============================================================================

EXEMPT_ROUTES: List[str] = [
    # Health and status
    r"^/api/v[12]/health.*",
    r"^/health.*",
    r"^/ready.*",
    
    # Authentication
    r"^/api/v[12]/login.*",
    r"^/api/v[12]/logout.*",
    r"^/api/v[12]/register.*",
    r"^/api/v[12]/refresh.*",
    r"^/api/v[12]/auto[_-]?login.*",
    r"^/api/v[12]/token.*",
    
    # Feature API (users need to query their features)
    r"^/api/v[12]/features.*",
    
    # User profile (always accessible)
    r"^/api/v[12]/users/me$",
    r"^/api/v[12]/users/whoami$",
    
    # Basic flow operations (execution is handled separately)
    r"^/api/v[12]/flows$",  # List flows
    r"^/api/v[12]/flows/[^/]+$",  # Get/Create/Update single flow
    r"^/api/v[12]/run/.*",  # Flow execution (validated in service layer)
    r"^/api/v[12]/build/.*",  # Flow building
    
    # Folders (basic organization)
    r"^/api/v[12]/folders.*",
    
    # Starter projects
    r"^/api/v[12]/starter[_-]?projects.*",
    
    # Documentation
    r"^/docs.*",
    r"^/openapi\.json.*",
    r"^/redoc.*",
    
    # Static files
    r"^/static/.*",
    r"^/assets/.*",
    
    # Super Admin routes (handled by admin auth)
    r"^/api/v[12]/admin/.*",
    r"^/api/v[12]/superuser/.*",
    
    # License and tenant info (read-only)
    r"^/api/v[12]/license[_-]?tiers$",
    r"^/api/v[12]/tenants/me$",
]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_required_features(path: str) -> List[str]:
    """
    Get required features for a route path.
    
    Args:
        path: The request path (e.g., "/api/v2/mcp/servers")
    
    Returns:
        List of feature keys required (OR logic - any enables access).
        Empty list means no specific feature requirements.
    """
    # Check exemptions first
    for pattern in EXEMPT_ROUTES:
        if re.match(pattern, path, re.IGNORECASE):
            return []
    
    # Find matching feature requirements
    for pattern, features in ROUTE_FEATURE_MAP.items():
        if re.match(pattern, path, re.IGNORECASE):
            return features
    
    return []  # No specific requirements


def is_route_exempt(path: str) -> bool:
    """
    Check if a route is exempt from feature checks.
    
    Args:
        path: The request path
    
    Returns:
        True if the route should bypass feature enforcement
    """
    return any(re.match(pattern, path, re.IGNORECASE) for pattern in EXEMPT_ROUTES)


def get_all_protected_routes() -> Dict[str, List[str]]:
    """
    Get all protected routes and their requirements.
    Useful for documentation and auditing.
    
    Returns:
        Copy of ROUTE_FEATURE_MAP
    """
    return dict(ROUTE_FEATURE_MAP)


def get_all_exempt_routes() -> List[str]:
    """
    Get all exempt route patterns.
    Useful for documentation and auditing.
    
    Returns:
        Copy of EXEMPT_ROUTES
    """
    return list(EXEMPT_ROUTES)


def add_route_protection(pattern: str, features: List[str]) -> None:
    """
    Dynamically add route protection.
    Use sparingly - prefer static configuration.
    
    Args:
        pattern: Regex pattern for the route
        features: List of required features (OR logic)
    """
    ROUTE_FEATURE_MAP[pattern] = features


def remove_route_protection(pattern: str) -> bool:
    """
    Remove route protection.
    Use sparingly - prefer static configuration.
    
    Args:
        pattern: Regex pattern to remove
    
    Returns:
        True if pattern was removed, False if not found
    """
    if pattern in ROUTE_FEATURE_MAP:
        del ROUTE_FEATURE_MAP[pattern]
        return True
    return False


