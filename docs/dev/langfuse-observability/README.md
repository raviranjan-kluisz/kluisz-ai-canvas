# Langfuse Observability Integration

## Overview

This document describes the complete integration of Langfuse for observability, tracing, and usage analytics in Kluisz Kanvas. The system captures comprehensive trace data, calculates costs and credits, and provides detailed usage statistics for tenants and users.

## Implementation Status: ✅ COMPLETE

The following components have been implemented:

| Component | Status | Location |
|-----------|--------|----------|
| Langfuse Tracer Enhancement | ✅ | `src/backend/base/kluisz/services/tracing/langfuse.py` |
| LangfuseClientService | ✅ | `src/backend/base/kluisz/services/langfuse/client.py` |
| PricingEngine | ✅ | `src/backend/base/kluisz/services/pricing/engine.py` |
| AnalyticsService | ✅ | `src/backend/base/kluisz/services/analytics/service.py` |
| Credit Enforcement | ✅ | `src/backend/base/kluisz/services/credits/enforcement.py` |
| Analytics API | ✅ | `src/backend/base/kluisz/api/v2/analytics.py` |
| Frontend Query Hooks | ✅ | `src/frontend/src/controllers/API/queries/analytics/` |
| Usage Dashboard | ✅ | `src/frontend/src/pages/SuperAdminPage/components/UsageDashboard/` |
| Credit Status Component | ✅ | `src/frontend/src/components/common/CreditStatus/` |

## Environment Variables

Set the following environment variables to enable Langfuse integration:

```bash
KLUISZ_LANGFUSE_SECRET_KEY=your_secret_key
KLUISZ_LANGFUSE_PUBLIC_KEY=your_public_key
KLUISZ_LANGFUSE_HOST=https://cloud.langfuse.com  # or your self-hosted URL
```

## Documentation Structure

### Core Documentation

1. **[langfuse-tracer-enhancement.md](./langfuse-tracer-enhancement.md)**
   - How we enhance the Langfuse tracer
   - Metadata structure (tenant_id, kluisz_project_id, kluisz_flow_id)
   - Integration points and trace data capture

2. **[analytics-service.md](./analytics-service.md)**
   - How analytics service processes Langfuse traces
   - Updates to `tenant_usage_stats` and `user_usage_stats`
   - Credits calculation and transaction tracking
   - Statistics aggregation and dashboard data

3. **[pricing-engine.md](./pricing-engine.md)**
   - Cost calculation from token usage
   - Credits conversion using tier pricing
   - Model pricing configuration
   - Cost breakdown by model/user

4. **[frontend-dashboards-plan.md](./frontend-dashboards-plan.md)**
   - Frontend dashboard implementation plan
   - Platform Admin, Tenant Admin, and User views
   - Chart types and data visualization

5. **[implementation.md](./implementation.md)**
   - Step-by-step implementation guide
   - Code examples and integration points
   - Step-by-step implementation guide
   - Code examples and integration points
   - Testing procedures

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Kluisz Kanvas Application                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Flow Run   │  │  Component   │  │   LLM Call   │       │
│  │   Execution  │→ │  Execution   │→ │   Execution   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ LangfuseTracer  │                        │
│                   │  - tenant_id    │                        │
│                   │  - user_id      │                        │
│                   │  - kluisz_project_id │                  │
│                   │  - kluisz_flow_id    │                  │
│                   └────────┬────────┘                        │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             │ HTTP/API
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    Langfuse Cloud                              │
│  - Traces with metadata                                        │
│  - Usage metrics (tokens, cost, latency)                     │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Langfuse API
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          LangfuseClientService                                │
│  - Fetches traces/metrics from Langfuse                       │
│  - Filters by tenant_id, user_id, date range                │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Processed Traces
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          AnalyticsService                                    │
│  - Aggregates usage by tenant/user                          │
│  - Uses PricingEngine for cost/credits calculation           │
│  - Updates tenant_usage_stats                                │
│  - Updates user_usage_stats                                  │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Database Updates
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          Database Tables                                      │
│  - tenant_usage_stats (period_start, period_end)             │
│  - user_usage_stats (period_start, period_end)               │
│  - transaction (credit transactions)                         │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ API Responses
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          Frontend Dashboards                                  │
│  - Platform Admin View (all tenants)                          │
│  - Tenant Admin View (tenant-wide)                            │
│  - User View (personal usage)                                 │
└───────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Enhanced Langfuse Tracer

- **Location**: `src/backend/base/kluisz/services/tracing/langfuse.py`
- **Enhancements**: Adds tenant_id, kluisz_project_id, kluisz_flow_id to trace metadata
- **See**: [langfuse-tracer-enhancement.md](./langfuse-tracer-enhancement.md)

### 2. Analytics Service

- **Location**: `src/backend/base/kluisz/services/analytics/service.py`
- **Responsibilities**: 
  - Fetches traces from Langfuse
  - Aggregates usage statistics
  - Updates tenant_usage_stats and user_usage_stats
- **See**: [analytics-service.md](./analytics-service.md)

### 3. Pricing Engine

- **Location**: `src/backend/base/kluisz/services/pricing/engine.py`
- **Responsibilities**:
  - Calculates cost from token usage
  - Converts cost to credits using tier pricing
  - Applies tier-specific multipliers
- **See**: [pricing-engine.md](./pricing-engine.md)

### 4. Langfuse Client Service

- **Location**: `src/backend/base/kluisz/services/langfuse/client_service.py`
- **Responsibilities**: 
  - Interacts with Langfuse API
  - Fetches traces with filters
  - Retrieves usage metrics

## Data Flow

### 1. Trace Capture

1. Flow execution starts
2. LangfuseTracer initialized with tenant_id, kluisz_project_id, kluisz_flow_id
3. Traces sent to Langfuse with metadata
4. Langfuse stores traces with usage metrics (tokens, cost, latency)

### 2. Usage Statistics Update

1. Scheduled job triggers analytics update
2. AnalyticsService fetches traces from Langfuse for period
3. PricingEngine calculates costs and credits
4. Statistics aggregated by tenant and user
5. Database tables updated (tenant_usage_stats, user_usage_stats)
6. Credit transactions created

### 3. Dashboard Display

1. Frontend requests usage statistics via API
2. AnalyticsService queries database tables
3. Data formatted for dashboard display
4. Charts and tables rendered with usage data

## Usage Statistics Models

### Tenant Usage Stats

```python
class TenantUsageStats(SQLModel, table=True):
    tenant_id: UUIDstr
    period_start: datetime
    period_end: datetime
    total_credits_used: int
    total_traces: int
    total_cost_usd: Decimal
    active_users_count: int
```

### User Usage Stats

```python
class UserUsageStats(SQLModel, table=True):
    user_id: UUIDstr
    period_start: datetime
    period_end: datetime
    credits_used: int
    traces_count: int
    cost_usd: Decimal
```

## API Endpoints

### Analytics APIs

**Base Path:** `/api/v2/analytics`

- `GET /api/v2/analytics/platform/stats` - Platform-wide stats (super admin)
- `GET /api/v2/analytics/tenant/{tenant_id}/stats` - Tenant-wide stats
- `GET /api/v2/analytics/user/{user_id}/stats` - User-specific stats
- `GET /api/v2/analytics/time-series` - Time series data for charts
- `GET /api/v2/analytics/top-users` - Top users by usage
- `GET /api/v2/analytics/top-flows` - Top flows by usage
- `GET /api/v2/analytics/cost-breakdown` - Cost breakdown by model/tenant/user

## Prerequisites

⚠️ **IMPORTANT:** Before implementing Langfuse observability, ensure super admins are associated with tenants.

This is required because:
- Traces need `tenant_id` in metadata
- Usage analytics are tenant-scoped
- All users (including super admins) must belong to a tenant

## Quick Start

1. **Enhance Tracer**: See [langfuse-tracer-enhancement.md](./langfuse-tracer-enhancement.md)
2. **Build Analytics Service**: See [analytics-service.md](./analytics-service.md)
3. **Configure Pricing Engine**: See [pricing-engine.md](./pricing-engine.md)
4. **Implement Dashboards**: See [frontend-dashboards-plan.md](./frontend-dashboards-plan.md)
5. **Follow Implementation Guide**: See [implementation.md](./implementation.md)

## Related Documentation

- [Business Logic](../licensing-credits/business_logic.md) - Licensing and credits system
- [Complete ERD](../licensing-credits/complete_erd.md) - Database schema
