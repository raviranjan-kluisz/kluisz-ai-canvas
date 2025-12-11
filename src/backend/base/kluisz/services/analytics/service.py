"""Analytics Service - Fast Local Queries from Transaction Table.

This service provides analytics by querying the local transaction table,
which is populated in real-time by the KluiszMeteringCallback.

Benefits over previous Langfuse API approach:
- 100-1000x faster (local SQL vs external API)
- No rate limits or pagination issues
- Always up-to-date (real-time data)
- No external dependencies for billing/analytics

The transaction table contains all usage data:
- user_id, flow_id, tenant_id (via user)
- credits_amount, tokens, cost_usd (in metadata)
- timestamp for time-series queries
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from klx.log.logger import logger
from klx.services.deps import session_scope
from sqlmodel import select, func, and_, or_, cast, String
from sqlalchemy import text

from kluisz.schema.serialize import UUIDstr, str_to_uuid
from kluisz.services.base import Service


class AnalyticsService(Service):
    """Fast analytics service using local transaction queries.
    
    All data comes from the transaction table, which is populated
    in real-time by the metering callback during flow execution.
    """

    name = "analytics_service"

    @property
    def ready(self) -> bool:
        """Service is always ready (no external dependencies)."""
        return True

    async def get_tenant_dashboard_data(
        self,
        tenant_id: UUIDstr,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get dashboard data for tenant admin view.
        
        Fast local query - no Langfuse API calls!
        
        Returns:
        - Summary statistics (total tokens, cost, credits, executions)
        - Top users by usage
        - Top flows by usage
        - Time series data
        
        Args:
            tenant_id: Tenant ID
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)
        
        Returns:
            Dashboard data dictionary
        """
        from kluisz.services.database.models.transactions.model import TransactionTable
        from kluisz.services.database.models.user.model import User
        
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        async with session_scope() as session:
            # Get all users for this tenant
            user_stmt = select(User).where(User.tenant_id == str_to_uuid(tenant_id))
            user_result = await session.exec(user_stmt)
            users = list(user_result.all())
            user_ids = [u.id for u in users]
            
            if not user_ids:
                return self._empty_dashboard(start_date, end_date)
            
            # Query transactions for all tenant users
            stmt = select(TransactionTable).where(
                and_(
                    TransactionTable.user_id.in_(user_ids),
                    TransactionTable.transaction_type == "deduction",
                    TransactionTable.timestamp >= start_date,
                    TransactionTable.timestamp <= end_date,
                )
            )
            result = await session.exec(stmt)
            transactions = list(result.all())
            
            # Aggregate summary
            total_credits = 0
            total_tokens = 0
            total_cost = Decimal("0.00")
            user_usage: dict[str, dict] = {}
            flow_usage: dict[str, dict] = {}
            daily_usage: dict[str, dict] = {}
            model_usage: dict[str, dict] = {}
            active_users: set[str] = set()
            
            for tx in transactions:
                # Aggregate totals
                total_credits += tx.credits_amount or 0
                
                metadata = tx.transaction_metadata or {}
                tokens = metadata.get("total_tokens", 0) or 0
                cost = Decimal(str(metadata.get("cost_usd", 0) or 0))
                
                total_tokens += tokens
                total_cost += cost
                
                # Track by model (from model_usage in metadata)
                model_usage_data = metadata.get("model_usage", {})
                if isinstance(model_usage_data, dict):
                    for model, usage in model_usage_data.items():
                        if model not in model_usage:
                            model_usage[model] = {
                                "total_tokens": 0,
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "total_cost_usd": Decimal("0"),
                                "trace_count": 0,
                            }
                        model_usage[model]["total_tokens"] += usage.get("total_tokens", 0)
                        model_usage[model]["input_tokens"] += usage.get("input_tokens", 0)
                        model_usage[model]["output_tokens"] += usage.get("output_tokens", 0)
                        model_usage[model]["total_cost_usd"] += Decimal(str(usage.get("total_cost_usd", 0) or 0))
                        model_usage[model]["trace_count"] += usage.get("call_count", 1)
                
                # Track by user
                user_id_str = str(tx.user_id)
                active_users.add(user_id_str)
                if user_id_str not in user_usage:
                    user_usage[user_id_str] = {
                        "credits": 0, "tokens": 0, "cost_usd": Decimal("0"), "executions": 0
                    }
                user_usage[user_id_str]["credits"] += tx.credits_amount or 0
                user_usage[user_id_str]["tokens"] += tokens
                user_usage[user_id_str]["cost_usd"] += cost
                user_usage[user_id_str]["executions"] += 1
                
                # Track by flow
                if tx.flow_id:
                    flow_id_str = str(tx.flow_id)
                    if flow_id_str not in flow_usage:
                        flow_usage[flow_id_str] = {
                            "credits": 0, "tokens": 0, "cost_usd": Decimal("0"), "executions": 0
                        }
                    flow_usage[flow_id_str]["credits"] += tx.credits_amount or 0
                    flow_usage[flow_id_str]["tokens"] += tokens
                    flow_usage[flow_id_str]["cost_usd"] += cost
                    flow_usage[flow_id_str]["executions"] += 1
                
                # Track daily
                day_key = tx.timestamp.strftime("%Y-%m-%d")
                if day_key not in daily_usage:
                    daily_usage[day_key] = {
                        "date": day_key, "credits": 0, "tokens": 0, "cost_usd": Decimal("0"), "executions": 0
                    }
                daily_usage[day_key]["credits"] += tx.credits_amount or 0
                daily_usage[day_key]["tokens"] += tokens
                daily_usage[day_key]["cost_usd"] += cost
                daily_usage[day_key]["executions"] += 1
            
            # Build top users list with user info
            top_users = []
            for user_id_str, usage in user_usage.items():
                user = next((u for u in users if str(u.id) == user_id_str), None)
                if user:
                    top_users.append({
                        "user_id": user_id_str,
                        "username": user.username,
                        "credits_used": usage["credits"],
                        "tokens": usage["tokens"],
                        "cost_usd": float(usage["cost_usd"]),
                        "executions": usage["executions"],
                        "credits_allocated": user.credits_allocated or 0,
                        "credits_remaining": (user.credits_allocated or 0) - (user.credits_used or 0),
                    })
            top_users.sort(key=lambda x: x["executions"], reverse=True)
            
            # Build top flows list
            top_flows = [
                {
                    "flow_id": flow_id,
                    "credits_used": data["credits"],
                    "tokens": data["tokens"],
                    "cost_usd": float(data["cost_usd"]),
                    "executions": data["executions"],
                }
                for flow_id, data in flow_usage.items()
            ]
            top_flows.sort(key=lambda x: x["executions"], reverse=True)
            
            # Build time series
            time_series = sorted(
                [
                    {
                        "date": d["date"],
                        "credits": d["credits"],
                        "tokens": d["tokens"],
                        "cost_usd": float(d["cost_usd"]),
                        "executions": d["executions"],
                    }
                    for d in daily_usage.values()
                ],
                key=lambda x: x["date"]
            )
            
            # Build model usage summary
            by_model: dict[str, dict[str, Any]] = {}
            for model, usage in model_usage.items():
                by_model[model] = {
                    "total_tokens": usage["total_tokens"],
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "total_cost_usd": float(usage["total_cost_usd"]),
                    "trace_count": usage["trace_count"],
                }
            
            return {
                "summary": {
                    "total_executions": len(transactions),
                    "total_credits": total_credits,
                    "total_tokens": total_tokens,
                    "total_cost_usd": float(total_cost),
                    "active_users_count": len(active_users),
                },
                "top_users": top_users[:10],
                "top_flows": top_flows[:10],
                "time_series": time_series,
                "by_model": by_model,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            }

    async def get_user_dashboard_data(
        self,
        user_id: UUIDstr,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get dashboard data for user view.
        
        Fast local query - no Langfuse API calls!
        
        Returns:
        - Personal usage summary
        - Credits used/remaining
        - Top flows used
        - Time series data
        
        Args:
            user_id: User ID
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)
        
        Returns:
            Dashboard data dictionary
        """
        from kluisz.services.database.models.transactions.model import TransactionTable
        from kluisz.services.database.models.user.model import User
        
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        async with session_scope() as session:
            # Get user
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user_uuid = str_to_uuid(user_id)
            
            # Optimized: Use SQL aggregation for summary stats
            summary_stmt = select(
                func.count(TransactionTable.id).label("total_executions"),
                func.sum(TransactionTable.credits_amount).label("total_credits"),
            ).where(
                and_(
                    TransactionTable.user_id == user_uuid,
                    TransactionTable.transaction_type == "deduction",
                    TransactionTable.timestamp >= start_date,
                    TransactionTable.timestamp <= end_date,
                )
            )
            summary_result = await session.exec(summary_stmt)
            summary_row = summary_result.first()
            
            total_executions = summary_row.total_executions if summary_row and summary_row.total_executions else 0
            total_credits = summary_row.total_credits if summary_row and summary_row.total_credits else 0
            
            # Query transactions (optimized: only select needed fields)
            stmt = select(
                TransactionTable.flow_id,
                TransactionTable.credits_amount,
                TransactionTable.transaction_metadata,
                TransactionTable.timestamp,
            ).where(
                and_(
                    TransactionTable.user_id == user_uuid,
                    TransactionTable.transaction_type == "deduction",
                    TransactionTable.timestamp >= start_date,
                    TransactionTable.timestamp <= end_date,
                )
            )
            result = await session.exec(stmt)
            rows = list(result.all())
            
            # Aggregate in Python (metadata is JSON, can't aggregate in SQL easily)
            total_tokens = 0
            total_cost = Decimal("0.00")
            flow_usage: dict[str, dict] = {}
            daily_usage: dict[str, dict] = {}
            model_usage: dict[str, dict] = {}
            
            for row in rows:
                credits = row.credits_amount or 0
                metadata = row.transaction_metadata or {}
                tokens = metadata.get("total_tokens", 0) or 0
                cost = Decimal(str(metadata.get("cost_usd", 0) or 0))
                
                total_tokens += tokens
                total_cost += cost
                
                # Track by model (from model_usage in metadata)
                model_usage_data = metadata.get("model_usage", {})
                if isinstance(model_usage_data, dict):
                    for model, usage in model_usage_data.items():
                        if model not in model_usage:
                            model_usage[model] = {
                                "total_tokens": 0,
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "total_cost_usd": Decimal("0"),
                                "trace_count": 0,
                            }
                        model_usage[model]["total_tokens"] += usage.get("total_tokens", 0)
                        model_usage[model]["input_tokens"] += usage.get("input_tokens", 0)
                        model_usage[model]["output_tokens"] += usage.get("output_tokens", 0)
                        model_usage[model]["total_cost_usd"] += Decimal(str(usage.get("total_cost_usd", 0) or 0))
                        model_usage[model]["trace_count"] += usage.get("call_count", 1)
                
                # Track by flow
                if row.flow_id:
                    flow_id_str = str(row.flow_id)
                    if flow_id_str not in flow_usage:
                        flow_usage[flow_id_str] = {
                            "credits": 0, "tokens": 0, "cost_usd": Decimal("0"), "executions": 0
                        }
                    flow_usage[flow_id_str]["credits"] += credits
                    flow_usage[flow_id_str]["tokens"] += tokens
                    flow_usage[flow_id_str]["cost_usd"] += cost
                    flow_usage[flow_id_str]["executions"] += 1
                
                # Track daily
                day_key = row.timestamp.strftime("%Y-%m-%d")
                if day_key not in daily_usage:
                    daily_usage[day_key] = {
                        "date": day_key, "credits": 0, "tokens": 0, "cost_usd": Decimal("0"), "executions": 0
                    }
                daily_usage[day_key]["credits"] += credits
                daily_usage[day_key]["tokens"] += tokens
                daily_usage[day_key]["cost_usd"] += cost
                daily_usage[day_key]["executions"] += 1
            
            # Build top flows list
            top_flows = [
                {
                    "flow_id": flow_id,
                    "credits_used": data["credits"],
                    "tokens": data["tokens"],
                    "cost_usd": float(data["cost_usd"]),
                    "executions": data["executions"],
                }
                for flow_id, data in flow_usage.items()
            ]
            top_flows.sort(key=lambda x: x["executions"], reverse=True)
            
            # Build time series
            time_series = sorted(
                [
                    {
                        "date": d["date"],
                        "credits": d["credits"],
                        "tokens": d["tokens"],
                        "cost_usd": float(d["cost_usd"]),
                        "executions": d["executions"],
                    }
                    for d in daily_usage.values()
                ],
                key=lambda x: x["date"]
            )
            
            # Build model usage summary
            by_model: dict[str, dict[str, Any]] = {}
            for model, usage in model_usage.items():
                by_model[model] = {
                    "total_tokens": usage["total_tokens"],
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "total_cost_usd": float(usage["total_cost_usd"]),
                    "trace_count": usage["trace_count"],
                }
            
            return {
                "summary": {
                    "total_executions": total_executions,
                    "total_credits": total_credits,
                    "total_tokens": total_tokens,
                    "total_cost_usd": float(total_cost),
                },
                "credits": {
                    "credits_allocated": user.credits_allocated or 0,
                    "credits_used": user.credits_used or 0,
                    "credits_remaining": (user.credits_allocated or 0) - (user.credits_used or 0),
                    "credits_per_month": user.credits_per_month,
                    "license_is_active": user.license_is_active,
                },
                "top_flows": top_flows[:10],
                "time_series": time_series,
                "by_model": by_model,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            }

    async def get_platform_dashboard_data(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get dashboard data for platform admin (super admin) view.
        
        Fast local query - no Langfuse API calls!
        
        Returns:
        - Platform-wide statistics
        - Top tenants by usage
        - Time series data
        
        Args:
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)
        
        Returns:
            Platform dashboard data dictionary
        """
        from kluisz.services.database.models.transactions.model import TransactionTable
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.tenant.model import Tenant
        
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        async with session_scope() as session:
            # Get all active tenants
            tenant_stmt = select(Tenant).where(Tenant.is_active == True)
            tenant_result = await session.exec(tenant_stmt)
            tenants = list(tenant_result.all())
            tenant_map = {t.id: t for t in tenants}
            
            # Get all users
            user_stmt = select(User)
            user_result = await session.exec(user_stmt)
            users = list(user_result.all())
            user_tenant_map = {u.id: u.tenant_id for u in users}
            
            # Query all deduction transactions
            stmt = select(TransactionTable).where(
                and_(
                    TransactionTable.transaction_type == "deduction",
                    TransactionTable.timestamp >= start_date,
                    TransactionTable.timestamp <= end_date,
                )
            )
            result = await session.exec(stmt)
            transactions = list(result.all())
            
            # Aggregate
            total_credits = 0
            total_tokens = 0
            total_cost = Decimal("0.00")
            tenant_usage: dict[UUID, dict] = {}
            daily_usage: dict[str, dict] = {}
            model_usage: dict[str, dict] = {}
            active_users: set[str] = set()
            
            for tx in transactions:
                total_credits += tx.credits_amount or 0
                
                metadata = tx.transaction_metadata or {}
                tokens = metadata.get("total_tokens", 0) or 0
                cost = Decimal(str(metadata.get("cost_usd", 0) or 0))
                
                total_tokens += tokens
                total_cost += cost
                active_users.add(str(tx.user_id))
                
                # Track by model (from model_usage in metadata)
                model_usage_data = metadata.get("model_usage", {})
                if isinstance(model_usage_data, dict):
                    for model, usage in model_usage_data.items():
                        if model not in model_usage:
                            model_usage[model] = {
                                "total_tokens": 0,
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "total_cost_usd": Decimal("0"),
                                "trace_count": 0,
                            }
                        model_usage[model]["total_tokens"] += usage.get("total_tokens", 0)
                        model_usage[model]["input_tokens"] += usage.get("input_tokens", 0)
                        model_usage[model]["output_tokens"] += usage.get("output_tokens", 0)
                        model_usage[model]["total_cost_usd"] += Decimal(str(usage.get("total_cost_usd", 0) or 0))
                        model_usage[model]["trace_count"] += usage.get("call_count", 1)
                
                # Track by tenant
                tenant_id = user_tenant_map.get(tx.user_id)
                if tenant_id:
                    if tenant_id not in tenant_usage:
                        tenant_usage[tenant_id] = {
                            "credits": 0, "tokens": 0, "cost_usd": Decimal("0"), 
                            "executions": 0, "active_users": set()
                        }
                    tenant_usage[tenant_id]["credits"] += tx.credits_amount or 0
                    tenant_usage[tenant_id]["tokens"] += tokens
                    tenant_usage[tenant_id]["cost_usd"] += cost
                    tenant_usage[tenant_id]["executions"] += 1
                    tenant_usage[tenant_id]["active_users"].add(str(tx.user_id))
                
                # Track daily
                day_key = tx.timestamp.strftime("%Y-%m-%d")
                if day_key not in daily_usage:
                    daily_usage[day_key] = {
                        "date": day_key, "credits": 0, "tokens": 0, 
                        "cost_usd": Decimal("0"), "executions": 0
                    }
                daily_usage[day_key]["credits"] += tx.credits_amount or 0
                daily_usage[day_key]["tokens"] += tokens
                daily_usage[day_key]["cost_usd"] += cost
                daily_usage[day_key]["executions"] += 1
            
            # Build top tenants list
            top_tenants = []
            for tenant_id, usage in tenant_usage.items():
                tenant = tenant_map.get(tenant_id)
                if tenant:
                    top_tenants.append({
                        "tenant_id": str(tenant_id),
                        "tenant_name": tenant.name,
                        "tenant_slug": tenant.slug,
                        "credits_used": usage["credits"],
                        "tokens": usage["tokens"],
                        "cost_usd": float(usage["cost_usd"]),
                        "executions": usage["executions"],
                        "active_users_count": len(usage["active_users"]),
                    })
            top_tenants.sort(key=lambda x: x["executions"], reverse=True)
            
            # Build time series
            time_series = sorted(
                [
                    {
                        "date": d["date"],
                        "credits": d["credits"],
                        "tokens": d["tokens"],
                        "cost_usd": float(d["cost_usd"]),
                        "executions": d["executions"],
                    }
                    for d in daily_usage.values()
                ],
                key=lambda x: x["date"]
            )
            
            # Build model usage summary
            by_model: dict[str, dict[str, Any]] = {}
            for model, usage in model_usage.items():
                by_model[model] = {
                    "total_tokens": usage["total_tokens"],
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "total_cost_usd": float(usage["total_cost_usd"]),
                    "trace_count": usage["trace_count"],
                }
            
            return {
                "summary": {
                    "total_tenants": len(tenants),
                    "total_executions": len(transactions),
                    "total_credits": total_credits,
                    "total_tokens": total_tokens,
                    "total_cost_usd": float(total_cost),
                    "total_active_users": len(active_users),
                },
                "top_tenants": top_tenants[:10],
                "time_series": time_series,
                "by_model": by_model,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            }

    async def get_credit_status(self, user_id: UUIDstr) -> dict[str, Any]:
        """Get current credit status for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Credit status dictionary
        """
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.license_tier.model import LicenseTier
        
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            tier_name = None
            if user.license_tier_id:
                tier = await session.get(LicenseTier, user.license_tier_id)
                if tier:
                    tier_name = tier.name
            
            credits_allocated = user.credits_allocated or 0
            credits_used = user.credits_used or 0
            credits_remaining = credits_allocated - credits_used
            
            # Calculate usage percentage
            usage_percent = 0
            if credits_allocated > 0:
                usage_percent = round((credits_used / credits_allocated) * 100, 1)
            
            return {
                "user_id": str(user.id),
                "username": user.username,
                "credits_allocated": credits_allocated,
                "credits_used": credits_used,
                "credits_remaining": credits_remaining,
                "credits_per_month": user.credits_per_month,
                "usage_percent": usage_percent,
                "license_is_active": user.license_is_active,
                "license_tier_id": str(user.license_tier_id) if user.license_tier_id else None,
                "tier_name": tier_name,
                "is_low_credits": credits_remaining < (credits_allocated * 0.2) if credits_allocated > 0 else False,
                "is_out_of_credits": credits_remaining <= 0,
            }

    async def get_tenant_user_usage(
        self,
        tenant_id: UUIDstr,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get per-user usage breakdown for a tenant.
        
        Args:
            tenant_id: Tenant ID
            start_date: Start date
            end_date: End date
        
        Returns:
            List of user usage dictionaries
        """
        from kluisz.services.database.models.transactions.model import TransactionTable
        from kluisz.services.database.models.user.model import User
        
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        async with session_scope() as session:
            # Get users for tenant
            user_stmt = select(User).where(User.tenant_id == str_to_uuid(tenant_id))
            user_result = await session.exec(user_stmt)
            users = list(user_result.all())
            
            user_usage = []
            for user in users:
                # Query transactions for this user
                stmt = select(TransactionTable).where(
                    and_(
                        TransactionTable.user_id == user.id,
                        TransactionTable.transaction_type == "deduction",
                        TransactionTable.timestamp >= start_date,
                        TransactionTable.timestamp <= end_date,
                    )
                )
                result = await session.exec(stmt)
                transactions = list(result.all())
                
                total_credits = 0
                total_tokens = 0
                total_cost = Decimal("0.00")
                
                for tx in transactions:
                    total_credits += tx.credits_amount or 0
                    metadata = tx.transaction_metadata or {}
                    total_tokens += metadata.get("total_tokens", 0) or 0
                    total_cost += Decimal(str(metadata.get("cost_usd", 0) or 0))
                
                user_usage.append({
                    "user_id": str(user.id),
                    "username": user.username,
                    "executions": len(transactions),
                    "credits_used": total_credits,
                    "tokens": total_tokens,
                    "cost_usd": float(total_cost),
                    "credits_allocated": user.credits_allocated or 0,
                    "credits_remaining": (user.credits_allocated or 0) - (user.credits_used or 0),
                    "license_is_active": user.license_is_active,
                })
            
            # Sort by executions
            user_usage.sort(key=lambda x: x["executions"], reverse=True)
            return user_usage

    def _empty_dashboard(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Return empty dashboard structure."""
        return {
            "summary": {
                "total_executions": 0,
                "total_credits": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "active_users_count": 0,
            },
            "top_users": [],
            "top_flows": [],
            "time_series": [],
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        }

    async def teardown(self) -> None:
        """Cleanup resources (none needed for local queries)."""
        pass
