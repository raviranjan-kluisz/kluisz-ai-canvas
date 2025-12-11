from decimal import Decimal
from enum import Enum
from typing import Any

from kluisz.services.database.models.license.model import LicenseTier


# Default tier configurations
TIER_CONFIGS: dict[LicenseTier, dict[str, Any]] = {
    LicenseTier.BASIC: {
        "max_users": 5,
        "max_flows": 20,
        "max_api_calls": 1000,
        "credits": 1000,
        "credits_per_month": 1000,
        "price": Decimal("29.00"),
        "features": {
            "api_access": True,
            "webhook_support": False,
            "custom_components": False,
            "priority_support": False,
            "advanced_analytics": False,
        },
    },
    LicenseTier.PRO: {
        "max_users": 25,
        "max_flows": 100,
        "max_api_calls": 10000,
        "credits": 10000,
        "credits_per_month": 10000,
        "price": Decimal("99.00"),
        "features": {
            "api_access": True,
            "webhook_support": True,
            "custom_components": True,
            "priority_support": True,
            "advanced_analytics": False,
        },
    },
    LicenseTier.ENTERPRISE: {
        "max_users": None,  # Unlimited
        "max_flows": None,  # Unlimited
        "max_api_calls": None,  # Unlimited
        "credits": 100000,
        "credits_per_month": 100000,
        "price": Decimal("499.00"),
        "features": {
            "api_access": True,
            "webhook_support": True,
            "custom_components": True,
            "priority_support": True,
            "advanced_analytics": True,
            "sso": True,
            "custom_branding": True,
        },
    },
}


def get_tier_config(tier: LicenseTier) -> dict[str, Any]:
    """Get configuration for a specific tier"""
    return TIER_CONFIGS.get(tier, TIER_CONFIGS[LicenseTier.BASIC])


def create_license_from_tier(tenant_id: str, tier: LicenseTier) -> dict[str, Any]:
    """Create license data from tier configuration"""
    config = get_tier_config(tier)
    return {
        "tenant_id": tenant_id,
        "license_type": tier.value,
        "tier": tier,
        "max_users": config["max_users"],
        "max_flows": config["max_flows"],
        "max_api_calls": config["max_api_calls"],
        "credits": config["credits"],
        "credits_per_month": config["credits_per_month"],
        "credits_used": 0,
        "features": config["features"],
        "billing_cycle": "monthly",
        "price": config["price"],
        "is_active": True,
    }
