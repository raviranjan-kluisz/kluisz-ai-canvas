"""Analytics API endpoints - Fast local queries from transaction table.

All analytics data comes from the local transaction table, which is
populated in real-time by the metering callback during flow execution.

Benefits:
- 100-1000x faster than Langfuse API queries
- No rate limits or pagination issues
- Always up-to-date (real-time data)
- No external dependencies
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from kluisz.api.utils import CurrentActiveUser
from kluisz.services.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService()


# ==================== Platform Analytics (Super Admin) ====================

@router.get("/platform/dashboard")
async def get_platform_dashboard(
    current_user: CurrentActiveUser,
    start_date: datetime | None = Query(None, description="Start date for analytics"),
    end_date: datetime | None = Query(None, description="End date for analytics"),
) -> dict[str, Any]:
    """Get platform-wide dashboard data for super admins.
    
    Fast local query - no external API calls!
    
    Returns:
    - Platform-wide statistics (executions, credits, tokens, cost)
    - Top tenants by usage
    - Time series data
    """
    if not current_user.is_platform_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform super admins can access platform analytics"
        )
    
    analytics_service = get_analytics_service()
    return await analytics_service.get_platform_dashboard_data(
        start_date=start_date,
        end_date=end_date,
    )


# ==================== Tenant Analytics (Tenant Admin) ====================

@router.get("/tenant/{tenant_id}/dashboard")
async def get_tenant_dashboard(
    tenant_id: str,
    current_user: CurrentActiveUser,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
) -> dict[str, Any]:
    """Get tenant dashboard data.
    
    Fast local query - no external API calls!
    
    Accessible by:
    - Platform super admins (any tenant)
    - Tenant admins (own tenant only)
    """
    # Check permissions
    if not current_user.is_platform_superadmin:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own tenant's analytics"
            )
        if not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can access tenant analytics"
            )
    
    analytics_service = get_analytics_service()
    return await analytics_service.get_tenant_dashboard_data(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/tenant/{tenant_id}/users")
async def get_tenant_user_usage(
    tenant_id: str,
    current_user: CurrentActiveUser,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
) -> list[dict[str, Any]]:
    """Get per-user usage breakdown for tenant.
    
    Returns usage stats for each user in the tenant.
    """
    # Check permissions
    if not current_user.is_platform_superadmin:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own tenant's data"
            )
        if not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can access user analytics"
            )
    
    analytics_service = get_analytics_service()
    return await analytics_service.get_tenant_user_usage(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )


# ==================== User Analytics ====================

@router.get("/user/dashboard")
async def get_user_dashboard(
    current_user: CurrentActiveUser,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
) -> dict[str, Any]:
    """Get current user's dashboard data.
    
    Fast local query - no external API calls!
    """
    analytics_service = get_analytics_service()
    return await analytics_service.get_user_dashboard_data(
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/user/{user_id}/dashboard")
async def get_specific_user_dashboard(
    user_id: str,
    current_user: CurrentActiveUser,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
) -> dict[str, Any]:
    """Get specific user's dashboard data (admin only)."""
    # Check permissions
    if not current_user.is_platform_superadmin:
        if str(current_user.id) != user_id:
            # Allow tenant admins to view their tenant's users
            from klx.services.deps import session_scope
            from kluisz.services.database.models.user.model import User
            from kluisz.schema.serialize import str_to_uuid
            
            async with session_scope() as session:
                target_user = await session.get(User, str_to_uuid(user_id))
                if not target_user or target_user.tenant_id != current_user.tenant_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only view users in your tenant"
                    )
                if not current_user.is_tenant_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only tenant admins can view other users' analytics"
                    )
    
    analytics_service = get_analytics_service()
    return await analytics_service.get_user_dashboard_data(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )


# ==================== Credits API ====================

@router.get("/credits/status")
async def get_credit_status(
    current_user: CurrentActiveUser,
) -> dict[str, Any]:
    """Get current user's credit status."""
    analytics_service = get_analytics_service()
    return await analytics_service.get_credit_status(str(current_user.id))


@router.get("/credits/user/{user_id}/status")
async def get_user_credit_status(
    user_id: str,
    current_user: CurrentActiveUser,
) -> dict[str, Any]:
    """Get specific user's credit status (admin only)."""
    # Check permissions
    if not current_user.is_platform_superadmin:
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own credit status"
            )
    
    analytics_service = get_analytics_service()
    return await analytics_service.get_credit_status(user_id)


# Export router
analytics_router = router
