# Langfuse Frontend Dashboards - Implementation Plan

## Overview

This document outlines the comprehensive frontend dashboards for displaying Langfuse observability data with different views for Platform Admin, Tenant Admin, and Regular Users.

## Langfuse Native Views

Langfuse provides several native views that we can leverage:

1. **Traces View** - Individual trace details with spans, tokens, cost
2. **Sessions View** - Grouped traces by session
3. **Users View** - User-level aggregation
4. **Scores View** - Feedback and scores
5. **Analytics Dashboard** - Aggregated metrics, charts, filters

## What We Need to Build

### Backend APIs (v2/analytics)

1. **GET /api/v2/analytics/platform/stats** - Platform-wide stats (super admin)
2. **GET /api/v2/analytics/tenant/{tenant_id}/stats** - Tenant-wide stats
3. **GET /api/v2/analytics/user/{user_id}/stats** - User-specific stats
4. **GET /api/v2/analytics/time-series** - Time series data for charts
5. **GET /api/v2/analytics/top-users** - Top users by usage
6. **GET /api/v2/analytics/top-flows** - Top flows by usage
7. **GET /api/v2/analytics/cost-breakdown** - Cost breakdown by model/tenant/user

### Frontend Components

#### 1. Platform Admin Dashboard (`SuperAdminPage`)

**Location:** `src/frontend/src/pages/SuperAdminPage/components/UsageDashboard/`

**Views:**
- **Overview Tab:**
  - Total tokens, cost, traces across all tenants
  - Usage trends (line chart)
  - Top 10 tenants by usage (table)
  - Active tenants count
  - Total users count

- **Tenants Tab:**
  - Table of all tenants with:
    - Tenant name, slug
    - Total usage (tokens, cost, traces)
    - User count
    - License tier
    - Credits remaining
    - Last activity
  - Click to drill down to tenant details

- **Analytics Tab:**
  - Time series charts:
    - Tokens over time (all tenants)
    - Cost over time
    - Traces over time
  - Filters:
    - Date range
    - Tenant filter
    - Metric type (tokens/cost/traces)

#### 2. Tenant Admin Dashboard (`TenantAdminPage`)

**Location:** `src/frontend/src/pages/TenantAdminPage/components/UsageDashboard/`

**Views:**
- **Overview:**
  - Tenant total usage (tokens, cost, traces)
  - Usage over time (chart)
  - Credits remaining
  - License tier info

- **Users Tab:**
  - Top users table:
    - Username
    - Total tokens
    - Total cost
    - Total traces
    - Last activity
  - Click to view user details

- **Flows Tab:**
  - Top flows table:
    - Flow name
    - Total tokens
    - Total cost
    - Total traces
    - Last used
  - Click to view flow details

- **Analytics Tab:**
  - Time series charts filtered to tenant
  - Cost breakdown by model
  - Usage by day/hour

#### 3. User Dashboard (`SettingsPage`)

**Location:** `src/frontend/src/pages/SettingsPage/components/UsageDashboard/`

**Views:**
- **My Usage:**
  - Personal total usage
  - Usage over time (chart)
  - Credits used/remaining
  - Usage projections

- **My Flows:**
  - Top flows I've used
  - Usage per flow
  - Last used dates

- **Activity:**
  - Recent traces
  - Daily usage breakdown
  - Cost breakdown

## Data Flow

```
Langfuse API
    ↓
UsageAnalyticsService (Backend)
    ↓
v2/analytics API Endpoints
    ↓
Frontend API Hooks (React Query)
    ↓
Dashboard Components
    ↓
Charts & Tables (Recharts/Chart.js)
```

## Key Metrics to Display

### From Langfuse Traces:
1. **Tokens:**
   - Total tokens (input + output)
   - Input tokens
   - Output tokens
   - Tokens by model

2. **Cost:**
   - Total cost (USD)
   - Cost by model
   - Cost by tenant/user
   - Cost trends

3. **Traces:**
   - Total trace count
   - Successful traces
   - Failed traces
   - Average latency

4. **Usage Patterns:**
   - Traces per day/hour
   - Peak usage times
   - Most used models
   - Most used flows

## Chart Types Needed

1. **Line Charts:**
   - Usage over time (tokens, cost, traces)
   - Multi-series for comparison

2. **Bar Charts:**
   - Top users/flows
   - Cost by model
   - Usage by day of week

3. **Pie Charts:**
   - Cost breakdown by model
   - Usage distribution

4. **Tables:**
   - Top users/flows
   - Detailed trace list
   - Tenant/user listings

## Filtering & Time Ranges

All dashboards should support:
- **Date Range:** Last 7 days, 30 days, 90 days, custom range
- **Time Granularity:** Hour, Day, Week, Month
- **Filters:**
  - By tenant (platform admin)
  - By user (tenant admin)
  - By flow
  - By model
  - By status (success/failure)

## Implementation Priority

1. ✅ Backend: UsageAnalyticsService
2. ✅ Backend: v2/analytics API endpoints
3. ✅ Frontend: API hooks for analytics
4. ✅ Frontend: Basic dashboard components
5. ✅ Frontend: Charts integration
6. ✅ Frontend: Platform Admin view
7. ✅ Frontend: Tenant Admin view
8. ✅ Frontend: User view

## Technology Stack

- **Backend:** FastAPI, SQLModel, Langfuse SDK
- **Frontend:** React, TypeScript, TanStack Query, Recharts
- **Charts:** Recharts (or Chart.js)
- **UI:** shadcn/ui components

