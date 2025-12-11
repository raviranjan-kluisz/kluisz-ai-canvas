"""Billing and usage API endpoints - Transaction-based analytics.

All usage data comes from the transaction table, populated in real-time
by the metering callback during flow execution.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, func, and_

from kluisz.services.auth.utils import get_current_active_superuser, get_current_active_user
from kluisz.services.database.models.tenant.crud import get_all_tenants, get_tenant_by_id, get_tenant_user_count
from kluisz.services.database.models.user.crud import get_user_by_id
from kluisz.services.database.models.user.model import User
from kluisz.services.database.models.license_tier.model import LicenseTier
from kluisz.services.database.models.transactions.model import TransactionTable
from kluisz.api.utils import DbSession

router = APIRouter(prefix="/billing", tags=["Billing"])


# Type aliases
CurrentUser = Annotated[User, Depends(get_current_active_user)]
SuperAdmin = Annotated[User, Depends(get_current_active_superuser)]


def _default_start_date() -> date:
    return date.today() - timedelta(days=30)


def _default_end_date() -> date:
    return date.today()


async def _get_transaction_summary(
    session,
    user_ids: list[UUID] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Get transaction summary from local DB (fast!)"""
    conditions = [TransactionTable.transaction_type == "deduction"]
    
    if user_ids:
        conditions.append(TransactionTable.user_id.in_(user_ids))
    
    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        conditions.append(TransactionTable.timestamp >= start_dt)
    
    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        conditions.append(TransactionTable.timestamp <= end_dt)
    
    stmt = select(TransactionTable).where(and_(*conditions))
    result = await session.exec(stmt)
    transactions = list(result.all())
    
    total_credits = 0
    total_tokens = 0
    total_cost = Decimal("0.00")
    active_users = set()
    
    for tx in transactions:
        total_credits += tx.credits_amount or 0
        metadata = tx.transaction_metadata or {}
        total_tokens += metadata.get("total_tokens", 0) or 0
        total_cost += Decimal(str(metadata.get("cost_usd", 0) or 0))
        if tx.user_id:
            active_users.add(str(tx.user_id))
    
    return {
        "total_flow_runs": len(transactions),
        "total_credits_used": total_credits,
        "total_tokens": total_tokens,
        "total_cost_usd": float(total_cost),
        "active_users_count": len(active_users),
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
    }


@router.get("/tenant/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    start_date: date = Query(default_factory=_default_start_date),
    end_date: date = Query(default_factory=_default_end_date),
) -> dict:
    """Get tenant usage statistics for a date range."""
    # Check access
    if not current_user.is_platform_superadmin:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )

    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get all users for this tenant
    user_stmt = select(User).where(User.tenant_id == tenant_id)
    user_result = await session.exec(user_stmt)
    users = list(user_result.all())
    user_ids = [u.id for u in users]
    
    summary = await _get_transaction_summary(session, user_ids, start_date, end_date)
    
    return {
        "tenant_id": str(tenant_id),
        "tenant_name": tenant.name,
        **summary,
    }


@router.get("/tenant/{tenant_id}/usage/summary")
async def get_tenant_usage_summary(
    tenant_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    start_date: date = Query(default_factory=_default_start_date),
    end_date: date = Query(default_factory=_default_end_date),
) -> dict:
    """Get aggregated tenant usage summary."""
    # Check access
    if not current_user.is_platform_superadmin:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )

    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get all users for this tenant
    user_stmt = select(User).where(User.tenant_id == tenant_id)
    user_result = await session.exec(user_stmt)
    users = list(user_result.all())
    user_ids = [u.id for u in users]
    
    summary = await _get_transaction_summary(session, user_ids, start_date, end_date)
    summary["tenant_name"] = tenant.name
    
    # Add subscription/license info
    if tenant.subscription_tier_id:
        tier = await session.get(LicenseTier, tenant.subscription_tier_id)
        if tier:
            summary["license"] = {
                "tier": tier.name,
                "subscription_status": tenant.subscription_status,
                "license_count": tenant.subscription_license_count or 0,
            }
    
    return summary


@router.get("/user/{user_id}/usage")
async def get_user_usage(
    user_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    start_date: date = Query(default_factory=_default_start_date),
    end_date: date = Query(default_factory=_default_end_date),
) -> dict:
    """Get user usage statistics for a date range."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check access: user can see own, tenant admin can see tenant users, super admin can see all
    if not current_user.is_platform_superadmin:
        if current_user.id != user_id:
            if not (current_user.is_tenant_admin and current_user.tenant_id == user.tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )

    summary = await _get_transaction_summary(session, [user_id], start_date, end_date)
    
    return {
        "user_id": str(user_id),
        "username": user.username,
        **summary,
        "credits_allocated": user.credits_allocated or 0,
        "credits_used": user.credits_used or 0,
        "credits_remaining": (user.credits_allocated or 0) - (user.credits_used or 0),
    }


@router.get("/user/{user_id}/usage/summary")
async def get_user_usage_summary(
    user_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    start_date: date = Query(default_factory=_default_start_date),
    end_date: date = Query(default_factory=_default_end_date),
) -> dict:
    """Get aggregated user usage summary."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check access
    if not current_user.is_platform_superadmin:
        if current_user.id != user_id:
            if not (current_user.is_tenant_admin and current_user.tenant_id == user.tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )

    summary = await _get_transaction_summary(session, [user_id], start_date, end_date)
    summary["username"] = user.username
    summary["credits_allocated"] = user.credits_allocated or 0
    summary["credits_used"] = user.credits_used or 0
    summary["credits_remaining"] = (user.credits_allocated or 0) - (user.credits_used or 0)
    
    return summary


@router.get("/analytics/overview")
async def get_analytics_overview(
    current_user: CurrentUser,
    session: DbSession,
) -> dict:
    """Get analytics overview based on user role."""
    if current_user.is_platform_superadmin:
        # Super admin: all tenants overview - optimized with single query
        tenants = await get_all_tenants(session)
        
        # Get all user counts in one query
        stmt = select(
            User.tenant_id,
            func.count(User.id).label("user_count")
        ).where(User.tenant_id.isnot(None)).group_by(User.tenant_id)
        result = await session.execute(stmt)
        user_counts = {str(row.tenant_id): row.user_count for row in result.all()}
        
        # Get all subscription tiers in one query
        tier_ids = [t.subscription_tier_id for t in tenants if t.subscription_tier_id]
        tiers_dict = {}
        if tier_ids:
            stmt = select(LicenseTier).where(LicenseTier.id.in_(tier_ids))
            result = await session.execute(stmt)
            tiers_dict = {str(t.id): t for t in result.scalars().all()}
        
        tenant_data = []
        for tenant in tenants:
            user_count = user_counts.get(str(tenant.id), 0)
            tier = tiers_dict.get(str(tenant.subscription_tier_id)) if tenant.subscription_tier_id else None
            tenant_data.append({
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "is_active": tenant.is_active,
                "user_count": user_count,
                "max_users": tenant.max_users,
                "license": {
                    "tier": tier.name if tier else None,
                    "subscription_status": tenant.subscription_status,
                    "license_count": tenant.subscription_license_count or 0,
                } if tier else None,
            })
        
        return {
            "role": "super_admin",
            "total_tenants": len(tenants),
            "active_tenants": sum(1 for t in tenants if t.is_active),
            "total_users": sum(t["user_count"] for t in tenant_data),
            "tenants": tenant_data,
        }

    elif current_user.is_tenant_admin and current_user.tenant_id:
        # Tenant admin: own tenant overview
        tenant = await get_tenant_by_id(session, current_user.tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        user_count = await get_tenant_user_count(session, tenant.id)
        
        # Get subscription tier if exists
        tier = None
        if tenant.subscription_tier_id:
            tier = await session.get(LicenseTier, tenant.subscription_tier_id)
        
        # Get all users for this tenant
        user_stmt = select(User).where(User.tenant_id == tenant.id)
        user_result = await session.exec(user_stmt)
        users = list(user_result.all())
        user_ids = [u.id for u in users]
        
        # Get usage summary for last 30 days
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        usage_summary = await _get_transaction_summary(session, user_ids, start_date, end_date)

        return {
            "role": "tenant_admin",
            "tenant": {
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "is_active": tenant.is_active,
            },
            "user_count": user_count,
            "max_users": tenant.max_users,
            "license": {
                "tier": tier.name if tier else None,
                "subscription_status": tenant.subscription_status,
                "license_count": tenant.subscription_license_count or 0,
            } if tier else None,
            "usage_summary": usage_summary,
        }

    else:
        # Regular user: own usage
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        usage_summary = await _get_transaction_summary(session, [current_user.id], start_date, end_date)
        usage_summary["credits_allocated"] = current_user.credits_allocated or 0
        usage_summary["credits_used"] = current_user.credits_used or 0
        usage_summary["credits_remaining"] = (current_user.credits_allocated or 0) - (current_user.credits_used or 0)

        return {
            "role": "user",
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
            },
            "usage_summary": usage_summary,
        }
