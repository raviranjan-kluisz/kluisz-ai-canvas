# Analytics Service - Usage Statistics Updates

## Overview

This document describes how the Analytics Service processes Langfuse traces to update `tenant_usage_stats` and `user_usage_stats` tables with comprehensive usage statistics, credits costing, and pricing information.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Langfuse Cloud                                  │
│  - Traces with metadata (tenant_id, user_id, tokens, cost) │
│  - Real-time trace data                                      │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Langfuse API
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          LangfuseClientService                               │
│  - Fetches traces from Langfuse                              │
│  - Filters by tenant_id, user_id, date range                │
│  - Extracts usage metrics (tokens, cost, latency)            │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Processed Traces
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          AnalyticsService                                    │
│  - Aggregates usage by tenant/user                           │
│  - Calculates credits from tokens                            │
│  - Applies pricing engine for cost calculation              │
│  - Updates tenant_usage_stats                                │
│  - Updates user_usage_stats                                 │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Database Updates
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          Database Tables                                      │
│  - tenant_usage_stats (period_start, period_end)             │
│  - user_usage_stats (period_start, period_end)               │
│  - transaction (credit transactions)                         │
└───────────────────────────────────────────────────────────────┘
```

## Service Implementation

### Location

**File:** `src/backend/base/kluisz/services/analytics/service.py`

### Core Responsibilities

1. **Fetch traces from Langfuse** via `LangfuseClientService`
2. **Aggregate usage metrics** by tenant and user
3. **Calculate credits** from token usage using pricing engine
4. **Update statistics tables** with aggregated data
5. **Create credit transactions** for usage tracking

## Usage Statistics Models

### Tenant Usage Stats

**Model:** `TenantUsageStats`

```python
class TenantUsageStats(SQLModel, table=True):
    id: UUIDstr
    tenant_id: UUIDstr
    period_start: datetime  # Period start timestamp
    period_end: datetime    # Period end timestamp
    
    # Aggregated Stats
    total_credits_used: int = 0      # Total credits used in period
    total_traces: int = 0             # Total traces/flow executions
    total_cost_usd: Decimal = 0.00   # Total cost in USD
    active_users_count: int = 0      # Number of active users
    
    created_at: datetime
    updated_at: datetime
```

**Unique Constraint:** One stats record per tenant per period (`tenant_id`, `period_start`, `period_end`)

### User Usage Stats

**Model:** `UserUsageStats`

```python
class UserUsageStats(SQLModel, table=True):
    id: UUIDstr
    user_id: UUIDstr
    period_start: datetime  # Period start timestamp
    period_end: datetime    # Period end timestamp
    
    # Aggregated Stats
    credits_used: int = 0           # Credits used in period
    traces_count: int = 0           # Number of traces/flow executions
    cost_usd: Decimal = 0.00        # Cost in USD for period
    
    created_at: datetime
    updated_at: datetime
```

**Unique Constraint:** One stats record per user per period (`user_id`, `period_start`, `period_end`)

## Analytics Service Methods

### 1. Update Tenant Usage Stats

```python
async def update_tenant_usage_stats(
    self,
    tenant_id: UUIDstr,
    *,
    period_start: datetime,
    period_end: datetime,
) -> TenantUsageStats:
    """
    Update tenant usage statistics for a given period.
    
    Process:
    1. Fetch traces from Langfuse for tenant in period
    2. Aggregate tokens, cost, traces
    3. Calculate credits using pricing engine
    4. Count active users
    5. Create or update tenant_usage_stats record
    """
    # Fetch traces from Langfuse
    traces = await self.langfuse_client.get_traces(
        project_id=tenant.langfuse_project_id,
        tenant_id=tenant_id,
        start_date=period_start,
        end_date=period_end,
    )
    
    # Aggregate metrics
    total_tokens = 0
    total_cost = Decimal("0.00")
    total_traces = len(traces)
    active_users = set()
    
    for trace in traces:
        # Extract usage from trace
        usage = trace.get("usage", {})
        tokens = usage.get("totalTokens", 0) or 0
        cost = Decimal(str(usage.get("totalCost", 0) or 0))
        
        total_tokens += tokens
        total_cost += cost
        
        # Track active users
        if trace.get("user_id"):
            active_users.add(trace["user_id"])
    
    # Calculate credits using pricing engine
    from kluisz.services.pricing.engine import PricingEngine
    pricing_engine = PricingEngine(self.settings_service)
    
    # Get tenant's license tier for pricing
    tenant = await session.get(Tenant, tenant_id)
    user = await session.get(User, tenant.users[0].id) if tenant.users else None
    tier = await session.get(LicenseTier, user.license_tier_id) if user else None
    
    # Calculate credits from tokens
    credits_used = await pricing_engine.calculate_credits_from_tokens(
        tokens=total_tokens,
        tier_id=user.license_tier_id if user else None,
    )
    
    # Get or create stats record
    stats = await self._get_or_create_tenant_stats(
        session, tenant_id, period_start, period_end
    )
    
    # Update stats
    stats.total_credits_used = credits_used
    stats.total_traces = total_traces
    stats.total_cost_usd = total_cost
    stats.active_users_count = len(active_users)
    stats.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    return stats
```

### 2. Update User Usage Stats

```python
async def update_user_usage_stats(
    self,
    user_id: UUIDstr,
    *,
    period_start: datetime,
    period_end: datetime,
) -> UserUsageStats:
    """
    Update user usage statistics for a given period.
    
    Process:
    1. Fetch traces from Langfuse for user in period
    2. Aggregate tokens, cost, traces
    3. Calculate credits using pricing engine
    4. Create or update user_usage_stats record
    """
    # Get user and tenant
    user = await session.get(User, user_id)
    if not user or not user.tenant_id:
        raise ValueError(f"User {user_id} not found or has no tenant")
    
    tenant = await session.get(Tenant, user.tenant_id)
    
    # Fetch traces from Langfuse
    traces = await self.langfuse_client.get_traces(
        project_id=tenant.langfuse_project_id,
        tenant_id=str(user.tenant_id),
        user_id=user_id,
        start_date=period_start,
        end_date=period_end,
    )
    
    # Aggregate metrics
    total_tokens = 0
    total_cost = Decimal("0.00")
    total_traces = len(traces)
    
    for trace in traces:
        usage = trace.get("usage", {})
        tokens = usage.get("totalTokens", 0) or 0
        cost = Decimal(str(usage.get("totalCost", 0) or 0))
        
        total_tokens += tokens
        total_cost += cost
    
    # Calculate credits using pricing engine
    from kluisz.services.pricing.engine import PricingEngine
    pricing_engine = PricingEngine(self.settings_service)
    
    credits_used = await pricing_engine.calculate_credits_from_tokens(
        tokens=total_tokens,
        tier_id=user.license_tier_id,
    )
    
    # Get or create stats record
    stats = await self._get_or_create_user_stats(
        session, user_id, period_start, period_end
    )
    
    # Update stats
    stats.credits_used = credits_used
    stats.traces_count = total_traces
    stats.cost_usd = total_cost
    stats.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    return stats
```

### 3. Batch Update for Period

```python
async def update_usage_stats_for_period(
    self,
    *,
    period_start: datetime,
    period_end: datetime,
    tenant_id: UUIDstr | None = None,
) -> dict[str, Any]:
    """
    Batch update usage statistics for all tenants/users in a period.
    
    This is typically called by a scheduled job (e.g., daily/hourly).
    """
    async with session_scope() as session:
        # Get all tenants (or specific tenant)
        if tenant_id:
            tenants = [await session.get(Tenant, tenant_id)]
        else:
            stmt = select(Tenant)
            result = await session.exec(stmt)
            tenants = list(result.all())
        
        updated_tenants = 0
        updated_users = 0
        
        for tenant in tenants:
            # Update tenant stats
            await self.update_tenant_usage_stats(
                tenant_id=str(tenant.id),
                period_start=period_start,
                period_end=period_end,
            )
            updated_tenants += 1
            
            # Update stats for all users in tenant
            stmt = select(User).where(User.tenant_id == tenant.id)
            result = await session.exec(stmt)
            users = list(result.all())
            
            for user in users:
                await self.update_user_usage_stats(
                    user_id=str(user.id),
                    period_start=period_start,
                    period_end=period_end,
                )
                updated_users += 1
        
        return {
            "tenants_updated": updated_tenants,
            "users_updated": updated_users,
            "period_start": period_start,
            "period_end": period_end,
        }
```

## Credits Calculation

### Using Pricing Engine

The analytics service uses the pricing engine to convert tokens to credits:

```python
from kluisz.services.pricing.engine import PricingEngine

pricing_engine = PricingEngine(self.settings_service)

# Calculate credits from tokens
credits = await pricing_engine.calculate_credits_from_tokens(
    tokens=total_tokens,
    tier_id=user.license_tier_id,
)

# The pricing engine:
# 1. Gets tier's credits_per_usd
# 2. Calculates cost from tokens (using model pricing)
# 3. Converts cost to credits using credits_per_usd
# 4. Applies tier's pricing_multiplier if needed
```

See [pricing-engine.md](./pricing-engine.md) for detailed pricing logic.

## Credit Transactions

When usage is tracked, credit transactions are created:

```python
async def create_credit_transaction(
    self,
    user_id: UUIDstr,
    credits_amount: int,
    transaction_type: str,  # "deduction", "addition", "refund"
    usage_record_id: str | None = None,
) -> Transaction:
    """
    Create a credit transaction record.
    
    This tracks credit usage for billing and auditing.
    """
    user = await session.get(User, user_id)
    
    credits_before = user.credits_used or 0
    
    # Update user credits
    if transaction_type == "deduction":
        user.credits_used = (user.credits_used or 0) + credits_amount
    elif transaction_type == "addition":
        user.credits_allocated = (user.credits_allocated or 0) + credits_amount
    
    credits_after = user.credits_used or 0
    
    # Create transaction record
    transaction = Transaction(
        user_id=user_id,
        transaction_type=transaction_type,
        credits_amount=credits_amount,
        credits_before=credits_before,
        credits_after=credits_after,
        usage_record_id=usage_record_id,
        transaction_metadata={
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "tokens": total_tokens,
            "cost_usd": str(total_cost),
        },
    )
    
    session.add(transaction)
    await session.commit()
    return transaction
```

## Scheduled Updates

### Background Job

A scheduled job (e.g., Celery task, cron job) runs periodically to update stats:

```python
# Scheduled job (runs hourly or daily)
async def sync_usage_stats_job():
    """
    Scheduled job to sync usage statistics from Langfuse.
    
    Runs:
    - Hourly: Update current hour stats
    - Daily: Update previous day stats
    - Monthly: Update previous month stats
    """
    analytics_service = get_analytics_service()
    
    # Update for last hour
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(hours=1)
    period_end = now
    
    await analytics_service.update_usage_stats_for_period(
        period_start=period_start,
        period_end=period_end,
    )
```

## Statistics Aggregation

### Time Periods

Stats are aggregated by time periods:

- **Hourly**: `period_start` and `period_end` are same hour
- **Daily**: `period_start` is 00:00:00, `period_end` is 23:59:59
- **Weekly**: `period_start` is Monday 00:00:00, `period_end` is Sunday 23:59:59
- **Monthly**: `period_start` is 1st 00:00:00, `period_end` is last day 23:59:59

### Aggregation Logic

```python
# For tenant stats:
total_credits_used = sum(all user credits in tenant for period)
total_traces = count(all traces in tenant for period)
total_cost_usd = sum(all costs in tenant for period)
active_users_count = count(unique users with traces in period)

# For user stats:
credits_used = sum(all credits for user in period)
traces_count = count(all traces for user in period)
cost_usd = sum(all costs for user in period)
```

## Dashboard Data

The analytics service provides data for dashboards:

```python
async def get_tenant_dashboard_data(
    self,
    tenant_id: UUIDstr,
    *,
    start_date: datetime,
    end_date: datetime,
    group_by: str = "day",  # hour, day, week, month
) -> dict[str, Any]:
    """
    Get dashboard data for tenant admin view.
    
    Returns:
    - Time series data (usage over time)
    - Top users by usage
    - Top flows by usage
    - Cost breakdown
    """
    # Query tenant_usage_stats for period
    stmt = select(TenantUsageStats).where(
        TenantUsageStats.tenant_id == tenant_id,
        TenantUsageStats.period_start >= start_date,
        TenantUsageStats.period_end <= end_date,
    )
    result = await session.exec(stmt)
    stats_records = list(result.all())
    
    # Build time series
    time_series = []
    for stats in stats_records:
        time_series.append({
            "date": stats.period_start,
            "credits": stats.total_credits_used,
            "traces": stats.total_traces,
            "cost": float(stats.total_cost_usd),
        })
    
    # Get top users (from user_usage_stats)
    # Get top flows (from trace metadata)
    
    return {
        "time_series": time_series,
        "summary": {
            "total_credits": sum(s.total_credits_used for s in stats_records),
            "total_traces": sum(s.total_traces for s in stats_records),
            "total_cost": sum(s.total_cost_usd for s in stats_records),
        },
        "top_users": top_users,
        "top_flows": top_flows,
    }
```

## Next Steps

1. **Pricing Engine**: See [pricing-engine.md](./pricing-engine.md) for cost calculation details
2. **Frontend Dashboards**: See [frontend-dashboards-plan.md](./frontend-dashboards-plan.md) for UI implementation
3. **API Endpoints**: See [readme.md](./readme.md) for API reference

