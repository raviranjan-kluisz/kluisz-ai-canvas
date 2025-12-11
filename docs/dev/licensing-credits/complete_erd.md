# Complete ERD - Licensing & Credits System

## Overview

This document provides the complete Entity Relationship Diagram (ERD) for the optimized licensing and credits system, designed for high concurrency (100+ concurrent users) and low latency.

**See also**: 
- [business_logic.md](./business_logic.md) for complete business logic and edge cases
- [new_architecture.md](./new_architecture.md) for system flow and architecture overview

## Core Design Principles
1. **Denormalization**: Store calculated values to avoid expensive joins
2. **Single Table Queries**: Merge related data into single tables where possible
3. **Atomic Updates**: All related updates happen in single transactions
4. **Separate Stats Tables**: Time-series data separated to avoid lock contention
5. **No Redundant Tables**: Removed `license` and `user_license` tables - everything in `user` table

---

## Complete Table Schema

### 1. `user` Table
**Purpose**: Single source of truth for users and their licenses (merged from old `user_license` table)

```sql
CREATE TABLE user (
    -- Primary Identity
    id UUID PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    profile_image VARCHAR,
    
    -- Status & Permissions
    is_active BOOLEAN DEFAULT FALSE,
    is_platform_superadmin BOOLEAN DEFAULT FALSE,
    is_tenant_admin BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    
    -- Multi-tenant
    tenant_id UUID REFERENCES tenant(id),
    
    -- License Fields (merged from user_license table)
    license_pool_id UUID,  -- References tier_id in tenant.license_pools JSON
    license_tier_id UUID REFERENCES license_tier(id),
    credits_allocated INTEGER DEFAULT 0 CHECK (credits_allocated >= 0),
    credits_used INTEGER DEFAULT 0 CHECK (credits_used >= 0),
    credits_per_month INTEGER,
    license_assigned_at TIMESTAMP,
    license_assigned_by UUID REFERENCES user(id),
    license_expires_at TIMESTAMP,
    license_is_active BOOLEAN DEFAULT FALSE,
    
    -- Indexes for Performance
    INDEX idx_user_tenant_id (tenant_id),
    INDEX idx_user_license_pool_id (license_pool_id),
    INDEX idx_user_license_tier_id (license_tier_id),
    INDEX idx_user_license_active (license_is_active),
    INDEX idx_user_username (username)
);

-- Computed Properties (in application layer)
-- credits_remaining = credits_allocated - credits_used
-- has_active_license = license_is_active AND license_pool_id IS NOT NULL 
--   AND license_tier_id IS NOT NULL 
--   AND (license_expires_at IS NULL OR license_expires_at > NOW())
--   AND credits_remaining > 0
```

**Key Benefits**:
- Single query to get user + license info
- No joins needed for common operations
- Atomic updates (no cross-table transactions)
- Better for high concurrency

---

### 2. `license_tier` Table
**Purpose**: Defines license tiers (Basic, Pro, Enterprise, Super Admin, etc.)

```sql
CREATE TABLE license_tier (
    id UUID PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    
    -- Pricing
    token_price_per_1000 DECIMAL(10, 2) DEFAULT 0.0,
    credits_per_usd DECIMAL(10, 2) DEFAULT 0.0,
    pricing_multiplier DECIMAL(10, 2) DEFAULT 1.0,
    
    -- Default Credits
    default_credits INTEGER DEFAULT 0 CHECK (default_credits >= 0),
    default_credits_per_month INTEGER,
    
    -- Limits (NULL = unlimited)
    max_users INTEGER,
    max_flows INTEGER,
    max_api_calls INTEGER,
    
    -- Features
    features JSON DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_by UUID REFERENCES user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_license_tier_name (name),
    INDEX idx_license_tier_active (is_active)
);
```

**Example Tiers**:
- **Super Admin**: 1000 credits, unlimited everything
- **Enterprise**: 500 credits/month, high limits
- **Pro**: 100 credits/month, medium limits
- **Basic**: 10 credits/month, low limits

---

### 3. `tenant` Table (with merged license pools)
**Purpose**: Multi-tenant organization with license pools stored as JSON

```sql
CREATE TABLE tenant (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    max_users INTEGER DEFAULT 10,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- License Pools (merged from license_pool table)
    -- JSON structure: {tier_id: {total_count, available_count, assigned_count, created_by, created_at, updated_at}}
    license_pools JSON DEFAULT '{}',
    
    -- Subscription Fields (for monthly subscriptions)
    subscription_tier_id UUID REFERENCES license_tier(id),
    subscription_license_count INTEGER DEFAULT 0,
    subscription_status VARCHAR, -- 'active', 'cancelled', 'past_due', 'trialing', 'expired'
    subscription_start_date TIMESTAMP,
    subscription_end_date TIMESTAMP,
    subscription_renewal_date TIMESTAMP,
    subscription_payment_method_id VARCHAR, -- Stripe payment method ID
    subscription_amount DECIMAL(10, 2), -- Monthly amount
    subscription_currency VARCHAR DEFAULT 'USD',
    
    INDEX idx_tenant_slug (slug),
    INDEX idx_tenant_active (is_active),
    INDEX idx_tenant_subscription_status (subscription_status)
);
```

**License Pools JSON Structure**:
```json
{
  "tier_id_1": {
    "total_count": 10,
    "available_count": 5,
    "assigned_count": 5,
    "created_by": "user_id",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "tier_id_2": {
    "total_count": 20,
    "available_count": 15,
    "assigned_count": 5,
    "created_by": "user_id",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Key Benefits**:
- ✅ No separate table needed - pools stored in tenant
- ✅ One query to get tenant + all pools
- ✅ Atomic updates (update tenant.license_pools JSON)
- ✅ One pool per tier per tenant (enforced by JSON structure)
- ✅ Denormalized counts for performance

---

### 4. `subscription` Table
**Purpose**: Monthly subscription management for tenants

```sql
CREATE TABLE subscription (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    
    -- Subscription Details
    tier_id UUID REFERENCES license_tier(id),
    license_count INTEGER DEFAULT 0 CHECK (license_count >= 0),
    monthly_credits INTEGER DEFAULT 0 CHECK (monthly_credits >= 0),
    
    -- Billing
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR DEFAULT 'USD',
    billing_cycle VARCHAR DEFAULT 'monthly', -- 'monthly', 'yearly'
    
    -- Status
    status VARCHAR NOT NULL, -- 'active', 'cancelled', 'past_due', 'trialing', 'expired'
    
    -- Dates
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    renewal_date TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    -- Payment
    payment_method_id VARCHAR, -- Stripe payment method ID
    last_payment_date TIMESTAMP,
    next_payment_date TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_subscription_tenant_id (tenant_id),
    INDEX idx_subscription_status (status),
    INDEX idx_subscription_renewal_date (renewal_date),
    INDEX idx_subscription_next_payment (next_payment_date)
);
```

**Key Benefits**:
- Tracks subscription lifecycle
- Supports monthly and yearly billing
- Handles payment failures and renewals
- Links to tenant and tier

---

### 5. `subscription_history` Table
**Purpose**: Audit trail for subscription changes

```sql
CREATE TABLE subscription_history (
    id UUID PRIMARY KEY,
    subscription_id UUID NOT NULL REFERENCES subscription(id),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    
    -- Change Details
    action VARCHAR NOT NULL, -- 'created', 'upgraded', 'downgraded', 'cancelled', 'renewed', 'payment_failed'
    old_tier_id UUID,
    new_tier_id UUID,
    old_license_count INTEGER,
    new_license_count INTEGER,
    old_amount DECIMAL(10, 2),
    new_amount DECIMAL(10, 2),
    
    -- Metadata
    reason TEXT,
    changed_by UUID REFERENCES user(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_subscription_history_subscription_id (subscription_id),
    INDEX idx_subscription_history_tenant_id (tenant_id),
    INDEX idx_subscription_history_action (action)
);
```

**Purpose**:
- Complete audit trail of subscription changes
- Tracks upgrades, downgrades, cancellations
- Supports billing disputes and analysis

---

### 6. `transaction` Table (Unified)
**Purpose**: Single table for both flow execution transactions AND credit transactions

```sql
CREATE TABLE transaction (
    id UUID PRIMARY KEY,
    
    -- Flow Execution Fields (for flow transactions)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vertex_id VARCHAR NOT NULL,
    target_id VARCHAR,
    inputs JSON,
    outputs JSON,
    status VARCHAR NOT NULL,
    error TEXT,
    flow_id UUID REFERENCES flow(id),
    
    -- Credit Transaction Fields (for credit transactions)
    user_id UUID REFERENCES user(id),
    transaction_type VARCHAR,  -- 'deduction', 'addition', 'refund', 'purchase'
    credits_amount INTEGER CHECK (credits_amount >= 0),
    credits_before INTEGER CHECK (credits_before >= 0),
    credits_after INTEGER CHECK (credits_after >= 0),
    usage_record_id VARCHAR,
    transaction_metadata JSON,
    created_by UUID REFERENCES user(id),
    
    -- Indexes
    INDEX idx_transaction_flow_id (flow_id),
    INDEX idx_transaction_user_id (user_id),
    INDEX idx_transaction_timestamp (timestamp),
    INDEX idx_transaction_type (transaction_type)
);

-- Usage Patterns:
-- Flow Transaction: flow_id IS NOT NULL, user_id IS NULL, transaction_type IS NULL
-- Credit Transaction: user_id IS NOT NULL, transaction_type IS NOT NULL, flow_id IS NULL
```

**Key Benefits**:
- Single audit table for all transactions
- Can link credit transactions to flow executions via usage_record_id
- Unified querying and reporting

---

### 7. `tenant_usage_stats` Table
**Purpose**: Time-series statistics for tenants (separate to avoid lock contention)

```sql
CREATE TABLE tenant_usage_stats (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    
    -- Time Period
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Aggregated Stats
    total_credits_used INTEGER DEFAULT 0 CHECK (total_credits_used >= 0),
    total_traces INTEGER DEFAULT 0 CHECK (total_traces >= 0),
    total_cost_usd DECIMAL(10, 2) DEFAULT 0.0,
    active_users_count INTEGER DEFAULT 0 CHECK (active_users_count >= 0),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique: One record per tenant per period
    UNIQUE(tenant_id, period_start, period_end),
    
    INDEX idx_tenant_usage_tenant_id (tenant_id),
    INDEX idx_tenant_usage_period (period_start, period_end)
);
```

**Purpose**:
- Historical analytics
- Separate from tenant table (no lock contention)
- Can be updated asynchronously
- Supports reporting and dashboards

---

### 8. `user_usage_stats` Table
**Purpose**: Time-series statistics for users (separate to avoid lock contention)

```sql
CREATE TABLE user_usage_stats (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user(id),
    
    -- Time Period
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Aggregated Stats
    credits_used INTEGER DEFAULT 0 CHECK (credits_used >= 0),
    traces_count INTEGER DEFAULT 0 CHECK (traces_count >= 0),
    cost_usd DECIMAL(10, 2) DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique: One record per user per period
    UNIQUE(user_id, period_start, period_end),
    
    INDEX idx_user_usage_user_id (user_id),
    INDEX idx_user_usage_period (period_start, period_end)
);
```

---

## Removed Tables (No Longer Needed)

### ❌ `license` Table
**Status**: DISABLED (`table=False`)
**Reason**: Individual licenses are no longer tracked. License information is stored directly in the `user` table and managed via pools in `tenant.license_pools` JSON.

### ❌ `user_license` Table
**Status**: DISABLED (`table=False`)
**Reason**: Merged into `user` table. All license fields are now columns in the `user` table.

### ❌ `license_pool` Table
**Status**: DISABLED (`table=False`)
**Reason**: Merged into `tenant` table as JSON field. License pools are now stored in `tenant.license_pools` JSON with structure: `{tier_id: {total_count, available_count, assigned_count, ...}}`.

### ❌ `credit_transaction` Table
**Status**: DISABLED (`table=False`)
**Reason**: Merged into `transaction` table. Credit transactions are now stored in the unified `transaction` table with additional fields.

---

## Relationships Diagram

```
tenant (1) ──< (N) user
  │
  ├── license_pools (JSON) ──> {tier_id: pool_data}
  ├── subscription_tier_id ──> (1) license_tier
  └──< (1) subscription

subscription (1) ──> (1) license_tier (via tier_id)
subscription (1) ──< (N) subscription_history

user (1) ──> (1) license_tier (via license_tier_id)
user (1) ──> (1) tenant (via tenant_id, references tier_id in tenant.license_pools)
user (1) ──< (N) transaction (credit transactions)
user (1) ──< (N) user_usage_stats
user (1) ──< (N) flow
flow (1) ──< (N) transaction (flow execution transactions)

tenant (1) ──< (N) tenant_usage_stats
```

---

## Key Operations & Performance

### License Assignment (Atomic)
```sql
BEGIN TRANSACTION;
  -- Update user with license info
  UPDATE user SET 
    license_pool_id = ?,  -- tier_id
    license_tier_id = ?,
    credits_allocated = ?,
    credits_used = 0,
    license_is_active = TRUE,
    license_assigned_at = NOW(),
    license_assigned_by = ?,
    updated_at = NOW()
  WHERE id = ?;
  
  -- Update tenant license_pools JSON
  UPDATE tenant SET
    license_pools = json_set(
      license_pools,
      '$.tier_id.available_count',
      CAST(json_extract(license_pools, '$.tier_id.available_count') AS INTEGER) - 1
    ),
    license_pools = json_set(
      license_pools,
      '$.tier_id.assigned_count',
      CAST(json_extract(license_pools, '$.tier_id.assigned_count') AS INTEGER) + 1
    ),
    license_pools = json_set(
      license_pools,
      '$.tier_id.updated_at',
      datetime('now')
    ),
    updated_at = NOW()
  WHERE id = ?;
COMMIT;
```

### Credit Deduction (Atomic)
```sql
BEGIN TRANSACTION;
  UPDATE user SET
    credits_used = credits_used + ?,
    updated_at = NOW()
  WHERE id = ? AND credits_remaining >= ?;
  
  INSERT INTO transaction (
    user_id, transaction_type, credits_amount,
    credits_before, credits_after, usage_record_id
  ) VALUES (?, 'deduction', ?, ?, ?, ?);
COMMIT;
```

### Query User with License (Single Query)
```sql
SELECT 
  u.*,
  lt.name as tier_name,
  lt.default_credits,
  json_extract(t.license_pools, '$.tier_id.total_count') as pool_total,
  json_extract(t.license_pools, '$.tier_id.available_count') as pool_available
FROM user u
LEFT JOIN license_tier lt ON u.license_tier_id = lt.id
LEFT JOIN tenant t ON u.tenant_id = t.id
WHERE u.id = ?;
```

---

## Indexes Summary

### Critical Indexes for Performance
1. **user**: `tenant_id`, `license_pool_id` (tier_id), `license_tier_id`, `license_is_active`, `username`
2. **tenant**: `slug`, `is_active` (license_pools stored as JSON, no separate indexes needed)
3. **transaction**: `user_id`, `flow_id`, `timestamp`, `transaction_type`
4. **tenant_usage_stats**: `tenant_id`, `(period_start, period_end)`
5. **user_usage_stats**: `user_id`, `(period_start, period_end)`

---

## Concurrency Considerations

1. **Row-Level Locking**: Use `SELECT ... FOR UPDATE` for critical sections
2. **Atomic Updates**: All related updates in single transactions
3. **Denormalized Counts**: No expensive COUNT queries
4. **Separate Stats Tables**: No lock contention on main tables
5. **Indexed Foreign Keys**: Fast joins and lookups

---

## Migration Notes

When migrating from old schema:
1. Copy `user_license` data into `user` table columns
2. Drop `license` and `user_license` tables
3. Migrate `credit_transaction` data to `transaction` table
4. Update `license_pool` counts from `user` table
5. Create stats tables for historical data

---

## Summary

**Total Active Tables**: 8
- `user` (with merged license fields)
- `license_tier`
- `tenant` (with merged license_pools as JSON + subscription fields)
- `subscription` (monthly subscription management)
- `subscription_history` (subscription audit trail)
- `transaction` (unified for flow + credit)
- `tenant_usage_stats`
- `user_usage_stats`

**Removed Tables**: 4
- `license` (disabled)
- `user_license` (merged into `user`)
- `license_pool` (merged into `tenant` as JSON)
- `credit_transaction` (merged into `transaction`)

**Key Optimizations**:
- ✅ Single table queries for user + license
- ✅ License pools merged into tenant (no separate table)
- ✅ Denormalized counts in tenant.license_pools JSON
- ✅ Unified transaction table
- ✅ Separate stats tables for analytics
- ✅ Subscription management with audit trail
- ✅ Atomic updates for consistency
- ✅ Optimized indexes for performance
- ✅ Reduced table count (8 tables vs original 10+)

