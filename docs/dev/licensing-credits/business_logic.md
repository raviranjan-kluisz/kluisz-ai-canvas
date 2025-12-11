# Business Logic - Licensing & Credits System

## Overview

This document describes the complete business logic for the licensing and credits system, including all operations, edge cases, upgrade flows, payment processing, and subscription management.
# New Licensing & Credits System Architecture
This document describes the optimized licensing system architecture where:
1. **License Tiers** are custom-created by Super Admin (not fixed Basic/Pro/Enterprise)
2. **License Pools** are stored in tenant table as JSON (one pool per tier per tenant)
3. **Super Admin** manages all licenses across all tenants
4. **Tenant Admin** assigns licenses from their tenant's pool to users
## Key Design Decisions
- **Merged Tables**: `user_license` → `user`, `license_pool` → `tenant` (JSON), `credit_transaction` → `transaction`
- **Denormalized Counts**: Pool counts stored directly in tenant.license_pools JSON
- **Single Table Queries**: User + license data in one table, no joins needed
- **Atomic Updates**: All related updates in single transactions
## Architecture Flow

┌─────────────────────────────────────────────────────────────┐
│              Super Admin                                    │
│                                                              │
│  1. Create License Tiers                                    │
│     ├─ Tier Name: "Starter", "Professional", "Enterprise"  │
│     ├─ Pricing multipliers                                  │
│     ├─ Credits mapping                                       │
│     └─ Feature flags                                        │
│                                                              │
│  2. Create Tenant                                           │
│     └─→ Create License Pools in tenant.license_pools JSON  │
│         ├─ Assign licenses by tier                          │
│         │   ├─ Starter: 10 licenses (stored as JSON)       │
│         │   ├─ Professional: 5 licenses (stored as JSON)   │
│         │   └─ Enterprise: 2 licenses (stored as JSON)     │
│         └─ Each pool tracks: total, available, assigned    │
│                                                              │
│  3. Manage All Licenses                                      │
│     ├─ View all tenant pools (from tenant.license_pools)    │
│     ├─ View all user licenses (from user table)            │
│     ├─ Create/update license pools (update tenant JSON)     │
│     ├─ Block/deactivate/activate user licenses              │
│     └─ Modify pricing and tiers                             │
└───────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Tenant Admin                                   │
│                                                              │
│  1. View Tenant's License Pools                              │
│     └─ See available licenses by tier (from tenant JSON)     │
│                                                              │
│  2. Create Users                                            │
│                                                              │
│  3. Assign Licenses to Users                                │
│     └─ Select from available licenses in pool               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [License Lifecycle](#license-lifecycle)
3. [User License Assignment](#user-license-assignment)
4. [License Upgrades & Downgrades](#license-upgrades--downgrades)
5. [Tenant License Pool Management](#tenant-license-pool-management)
6. [Payment & Subscription Flow](#payment--subscription-flow)
7. [Monthly Subscription Model](#monthly-subscription-model)
8. [Edge Cases & Error Handling](#edge-cases--error-handling)
9. [Frontend Views](#frontend-views)
10. [API Operations](#api-operations)

---

## Core Concepts

### License Tier
A **License Tier** defines the characteristics of a license:
- **Name**: "Starter", "Professional", "Enterprise", "Super Admin"
- **Default Credits**: Initial credit allocation
- **Monthly Credits**: Recurring monthly allocation (for subscriptions)
- **Pricing**: Token pricing, USD pricing, multipliers
- **Limits**: Max users, max flows, max API calls
- **Features**: Feature flags and capabilities

### License Pool
A **License Pool** is stored in `tenant.license_pools` JSON and represents available licenses for a specific tier:
```json
{
  "tier_id": {
    "total_count": 10,
    "available_count": 5,
    "assigned_count": 5,
    "created_by": "user_id",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### User License
A **User License** is stored directly in the `user` table:
- `license_pool_id`: References tier_id in tenant.license_pools
- `license_tier_id`: References the license tier
- `credits_allocated`: Total credits assigned
- `credits_used`: Credits consumed
- `credits_per_month`: Monthly recurring credits (for subscriptions)
- `license_is_active`: Whether license is currently active

---

## License Lifecycle

### 1. License Tier Creation (Super Admin)

**Flow**:
1. Super Admin creates a new license tier
2. Sets default credits, monthly credits, pricing, limits, features
3. Tier is now available for pool creation

**Business Rules**:
- Tier name must be unique
- Default credits must be >= 0
- Monthly credits can be NULL (one-time licenses) or >= 0 (subscriptions)
- Pricing multipliers must be > 0

**Edge Cases**:
- ❌ Cannot delete tier if pools exist for it
- ❌ Cannot modify tier if active users have licenses from it (requires migration)
- ✅ Can deactivate tier (prevents new assignments)

### 2. Tenant License Pool Creation (Super Admin)

**Flow**:
1. Super Admin creates/updates tenant
2. Assigns license pools by tier in `tenant.license_pools` JSON
3. Each pool tracks: total, available, assigned counts

**Example**:
```json
{
  "starter_tier_id": {
    "total_count": 10,
    "available_count": 10,
    "assigned_count": 0,
    "created_by": "super_admin_id",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "professional_tier_id": {
    "total_count": 5,
    "available_count": 5,
    "assigned_count": 0,
    "created_by": "super_admin_id",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Business Rules**:
- Pool counts must satisfy: `total_count = available_count + assigned_count`
- Cannot reduce `total_count` below `assigned_count`
- Can only increase pools (add more licenses)

**Edge Cases**:
- ❌ Cannot set `total_count < assigned_count` (would invalidate existing assignments)
- ✅ Can increase `total_count` (adds to `available_count`)
- ✅ Can transfer licenses between tiers (requires user reassignment)

### 3. License Assignment to User (Tenant Admin)

**Flow**:
1. Tenant Admin views available licenses in their tenant's pools
2. Selects a user and a tier
3. System assigns license from pool to user

**Business Rules**:
- User must belong to the tenant
- Pool must have `available_count > 0` for selected tier
- User cannot have an active license (must unassign first)
- Credits allocated from tier's `default_credits`

**Atomic Operation**:
```sql
BEGIN TRANSACTION;
  -- 1. Update user with license
  UPDATE user SET
    license_pool_id = tier_id,
    license_tier_id = tier_id,
    credits_allocated = tier.default_credits,
    credits_used = 0,
    credits_per_month = tier.default_credits_per_month,
    license_is_active = TRUE,
    license_assigned_at = NOW(),
    license_assigned_by = tenant_admin_id,
    updated_at = NOW()
  WHERE id = user_id AND tenant_id = tenant_id;
  
  -- 2. Update tenant pool counts
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
  WHERE id = tenant_id;
COMMIT;
```

**Edge Cases**:
- ❌ User already has active license → Must unassign first
- ❌ Pool has no available licenses → Show error, suggest upgrade
- ❌ User belongs to different tenant → Access denied
- ✅ Can assign to inactive user (license activates user)

---

## License Upgrades & Downgrades

### User License Upgrade (Tenant Admin)

**Scenario**: Upgrade user from "Starter" to "Professional" tier

**Flow**:
1. Tenant Admin selects user with Starter license
2. Chooses "Professional" tier
3. System checks:
   - Professional pool has available licenses
   - User's current credits are preserved (or migrated)
4. System performs upgrade

**Business Rules**:
- **Credit Migration Options**:
  - **Option A**: Preserve existing credits (add new tier credits)
  - **Option B**: Reset credits (user gets new tier's default credits)
  - **Option C**: Prorate credits based on tier value
- Old tier's pool: `assigned_count--`, `available_count++`
- New tier's pool: `assigned_count++`, `available_count--`
- Update user's `license_tier_id` and `license_pool_id`

**Atomic Operation**:
```sql
BEGIN TRANSACTION;
  -- 1. Get current license info
  SELECT license_tier_id, credits_allocated, credits_used 
  FROM user WHERE id = user_id;
  
  -- 2. Unassign from old tier pool
  UPDATE tenant SET
    license_pools = json_set(
      license_pools,
      '$.old_tier_id.assigned_count',
      CAST(json_extract(license_pools, '$.old_tier_id.assigned_count') AS INTEGER) - 1
    ),
    license_pools = json_set(
      license_pools,
      '$.old_tier_id.available_count',
      CAST(json_extract(license_pools, '$.old_tier_id.available_count') AS INTEGER) + 1
    )
  WHERE id = tenant_id;
  
  -- 3. Assign to new tier pool
  UPDATE tenant SET
    license_pools = json_set(
      license_pools,
      '$.new_tier_id.assigned_count',
      CAST(json_extract(license_pools, '$.new_tier_id.assigned_count') AS INTEGER) + 1
    ),
    license_pools = json_set(
      license_pools,
      '$.new_tier_id.available_count',
      CAST(json_extract(license_pools, '$.new_tier_id.available_count') AS INTEGER) - 1
    )
  WHERE id = tenant_id;
  
  -- 4. Update user license (preserve credits or reset)
  UPDATE user SET
    license_tier_id = new_tier_id,
    license_pool_id = new_tier_id,
    credits_allocated = CASE
      WHEN preserve_credits THEN credits_allocated + new_tier.default_credits
      ELSE new_tier.default_credits
    END,
    credits_per_month = new_tier.default_credits_per_month,
    updated_at = NOW()
  WHERE id = user_id;
  
  -- 5. Log upgrade transaction
  INSERT INTO transaction (
    user_id, transaction_type, credits_amount,
    credits_before, credits_after, transaction_metadata
  ) VALUES (
    user_id, 'upgrade', new_tier.default_credits,
    old_credits_allocated, new_credits_allocated,
    json_object('old_tier', old_tier_id, 'new_tier', new_tier_id)
  );
COMMIT;
```

**Edge Cases**:
- ❌ New tier pool has no available licenses → Block upgrade, suggest pool upgrade
- ❌ User has more credits than new tier allows → Option: preserve, reset, or prorate
- ✅ Can upgrade even if user has used credits (credits preserved or reset)
- ✅ Upgrade transaction logged for audit

### User License Downgrade (Tenant Admin)

**Scenario**: Downgrade user from "Professional" to "Starter" tier

**Flow**:
1. Tenant Admin selects user with Professional license
2. Chooses "Starter" tier
3. System checks:
   - User's current credits (may exceed new tier's default)
   - Starter pool has available licenses
4. System performs downgrade

**Business Rules**:
- **Credit Handling**:
  - If user has more credits than new tier default → Keep excess credits
  - If user has less → Keep current credits (don't reduce)
- Old tier's pool: `assigned_count--`, `available_count++`
- New tier's pool: `assigned_count++`, `available_count--`

**Edge Cases**:
- ✅ User keeps excess credits (grandfathered)
- ✅ Can downgrade even if credits exceed new tier default
- ⚠️ Warn user about potential credit loss if resetting

---

## Tenant License Pool Management

### Super Admin: Add Licenses to Tenant Pool

**Scenario**: Tenant needs more Professional licenses

**Flow**:
1. Super Admin views tenant's current pools
2. Selects tier (e.g., "Professional")
3. Enters number of additional licenses
4. System updates pool counts

**Business Rules**:
- Can only **increase** `total_count`
- Increase adds to `available_count`
- Cannot reduce below `assigned_count`

**Operation**:
```sql
UPDATE tenant SET
  license_pools = json_set(
    license_pools,
    '$.tier_id.total_count',
    CAST(json_extract(license_pools, '$.tier_id.total_count') AS INTEGER) + additional_count
  ),
  license_pools = json_set(
    license_pools,
    '$.tier_id.available_count',
    CAST(json_extract(license_pools, '$.tier_id.available_count') AS INTEGER) + additional_count
  ),
  license_pools = json_set(
    license_pools,
    '$.tier_id.updated_at',
    datetime('now')
  ),
  updated_at = NOW()
WHERE id = tenant_id;
```

**Edge Cases**:
- ✅ Can add licenses to any tier
- ✅ Increase is immediate (no payment required for manual assignment)
- ⚠️ Payment processing happens separately (see Payment Flow)

### Super Admin: Create New Pool for Tenant

**Scenario**: Tenant wants a new tier (e.g., "Enterprise")

**Flow**:
1. Super Admin creates/selects tier
2. Creates pool in tenant's `license_pools` JSON
3. Sets initial `total_count`

**Operation**:
```sql
UPDATE tenant SET
  license_pools = json_set(
    license_pools,
    '$.new_tier_id',
    json_object(
      'total_count', initial_count,
      'available_count', initial_count,
      'assigned_count', 0,
      'created_by', super_admin_id,
      'created_at', datetime('now'),
      'updated_at', datetime('now')
    )
  ),
  updated_at = NOW()
WHERE id = tenant_id;
```

**Edge Cases**:
- ❌ Cannot create pool if tier doesn't exist
- ✅ Pool created with all licenses available
- ✅ Can create multiple pools (one per tier)

---

## Payment & Subscription Flow

### Payment Processing

**Scenario**: Tenant pays for license upgrade or additional licenses

**Flow**:
1. Tenant Admin initiates payment
2. Payment processor (Stripe/PayPal) handles transaction
3. On success, webhook updates tenant pools
4. Transaction logged in `transaction` table

**Payment Types**:
- **One-time**: Purchase additional licenses
- **Subscription**: Monthly recurring for tier + licenses

**Business Rules**:
- Payment must be verified before pool update
- Failed payments don't update pools
- Refunds reduce pool counts (if applicable)

**Webhook Handler**:
```python
async def handle_payment_webhook(payment_event):
    if payment_event.type == "payment.succeeded":
        # Update tenant pools based on payment
        if payment_event.metadata.type == "license_purchase":
            await add_licenses_to_pool(
                tenant_id=payment_event.metadata.tenant_id,
                tier_id=payment_event.metadata.tier_id,
                count=payment_event.metadata.license_count
            )
        
        # Log transaction
        await create_transaction(
            user_id=payment_event.metadata.created_by,
            transaction_type="purchase",
            credits_amount=0,  # License purchase, not credit purchase
            transaction_metadata={
                "payment_id": payment_event.id,
                "tier_id": payment_event.metadata.tier_id,
                "license_count": payment_event.metadata.license_count,
                "amount": payment_event.amount
            }
        )
```

**Edge Cases**:
- ❌ Payment fails → No pool update, notify tenant admin
- ❌ Webhook received twice → Idempotent check (payment_id)
- ✅ Partial payment → Handle prorated licenses
- ✅ Refund → Reduce pool counts (if policy allows)

### Upgrade to License Tier

**Scenario**: Tenant upgrades from "Starter" to "Professional" tier

**Flow**:
1. Tenant Admin selects new tier
2. System calculates:
   - Price difference
   - Prorated amount (if mid-cycle)
   - Number of licenses to migrate
3. Payment processed
4. System upgrades:
   - Creates new pool for Professional tier
   - Migrates existing licenses (if applicable)
   - Updates all user licenses to new tier

**Business Rules**:
- **License Migration**:
  - Option A: Migrate all existing licenses to new tier
  - Option B: Keep old tier licenses, add new tier licenses
- **User License Migration**:
  - All users with old tier → upgraded to new tier
  - Credits preserved or reset based on policy
- **Proration**: Calculate based on remaining subscription period

**Edge Cases**:
- ❌ Cannot downgrade tier if users exceed new tier limits
- ✅ Can upgrade mid-cycle (prorated billing)
- ✅ Existing licenses migrated automatically
- ⚠️ Warn about credit changes during migration

---

## Monthly Subscription Model

### Subscription Structure

**Components**:
1. **Base Tier Subscription**: Monthly fee for tier access
2. **License Count Subscription**: Monthly fee per license
3. **Credit Top-up Subscription**: Monthly credit allocation

### ERD Updates for Subscriptions

**New Fields in `tenant` Table**:
```sql
ALTER TABLE tenant ADD COLUMN subscription_tier_id UUID REFERENCES license_tier(id);
ALTER TABLE tenant ADD COLUMN subscription_license_count INTEGER DEFAULT 0;
ALTER TABLE tenant ADD COLUMN subscription_status VARCHAR; -- 'active', 'cancelled', 'past_due', 'trialing'
ALTER TABLE tenant ADD COLUMN subscription_start_date TIMESTAMP;
ALTER TABLE tenant ADD COLUMN subscription_end_date TIMESTAMP;
ALTER TABLE tenant ADD COLUMN subscription_renewal_date TIMESTAMP;
ALTER TABLE tenant ADD COLUMN subscription_payment_method_id VARCHAR; -- Stripe payment method ID
ALTER TABLE tenant ADD COLUMN subscription_amount DECIMAL(10, 2); -- Monthly amount
ALTER TABLE tenant ADD COLUMN subscription_currency VARCHAR DEFAULT 'USD';
```

**New `subscription` Table**:
```sql
CREATE TABLE subscription (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    
    -- Subscription Details
    tier_id UUID REFERENCES license_tier(id),
    license_count INTEGER DEFAULT 0,
    monthly_credits INTEGER DEFAULT 0,
    
    -- Billing
    amount DECIMAL(10, 2) NOT NULL,
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
    INDEX idx_subscription_renewal_date (renewal_date)
);
```

**New `subscription_history` Table**:
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
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Subscription Lifecycle

**1. Subscription Creation**:
```sql
BEGIN TRANSACTION;
  -- Create subscription
  INSERT INTO subscription (
    tenant_id, tier_id, license_count, monthly_credits,
    amount, status, start_date, renewal_date, next_payment_date
  ) VALUES (...);
  
  -- Update tenant
  UPDATE tenant SET
    subscription_tier_id = tier_id,
    subscription_license_count = license_count,
    subscription_status = 'active',
    subscription_start_date = NOW(),
    subscription_renewal_date = DATE_ADD(NOW(), INTERVAL 1 MONTH),
    subscription_amount = amount
  WHERE id = tenant_id;
  
  -- Create initial pools
  UPDATE tenant SET
    license_pools = json_set(
      license_pools,
      '$.tier_id',
      json_object(
        'total_count', license_count,
        'available_count', license_count,
        'assigned_count', 0,
        'created_by', user_id,
        'created_at', datetime('now'),
        'updated_at', datetime('now')
      )
    )
  WHERE id = tenant_id;
  
  -- Log history
  INSERT INTO subscription_history (
    subscription_id, tenant_id, action, new_tier_id, new_license_count, new_amount
  ) VALUES (...);
COMMIT;
```

**2. Monthly Renewal**:
```sql
BEGIN TRANSACTION;
  -- Process payment
  -- On success:
  UPDATE subscription SET
    last_payment_date = NOW(),
    next_payment_date = DATE_ADD(NOW(), INTERVAL 1 MONTH),
    renewal_date = DATE_ADD(renewal_date, INTERVAL 1 MONTH),
    updated_at = NOW()
  WHERE id = subscription_id;
  
  -- Top up monthly credits for all users
  UPDATE user SET
    credits_allocated = credits_allocated + credits_per_month,
    updated_at = NOW()
  WHERE tenant_id = tenant_id 
    AND license_is_active = TRUE
    AND credits_per_month IS NOT NULL;
  
  -- Log renewal
  INSERT INTO subscription_history (
    subscription_id, tenant_id, action, changed_by
  ) VALUES (subscription_id, tenant_id, 'renewed', system_user_id);
COMMIT;
```

**3. Subscription Upgrade**:
```sql
BEGIN TRANSACTION;
  -- Calculate prorated amount
  -- Process payment
  
  -- Update subscription
  UPDATE subscription SET
    tier_id = new_tier_id,
    license_count = new_license_count,
    amount = new_amount,
    updated_at = NOW()
  WHERE id = subscription_id;
  
  -- Update tenant pools
  -- Migrate licenses, update counts
  
  -- Log upgrade
  INSERT INTO subscription_history (
    subscription_id, tenant_id, action,
    old_tier_id, new_tier_id,
    old_license_count, new_license_count,
    old_amount, new_amount
  ) VALUES (...);
COMMIT;
```

**4. Subscription Cancellation**:
```sql
BEGIN TRANSACTION;
  UPDATE subscription SET
    status = 'cancelled',
    cancelled_at = NOW(),
    end_date = renewal_date, -- Access until end of paid period
    updated_at = NOW()
  WHERE id = subscription_id;
  
  UPDATE tenant SET
    subscription_status = 'cancelled',
    subscription_end_date = renewal_date
  WHERE id = tenant_id;
  
  -- Log cancellation
  INSERT INTO subscription_history (
    subscription_id, tenant_id, action, reason, changed_by
  ) VALUES (subscription_id, tenant_id, 'cancelled', reason, user_id);
COMMIT;
```

**Edge Cases**:
- ❌ Payment fails → Mark as `past_due`, send notification
- ❌ Multiple failed payments → Cancel subscription, revoke access
- ✅ Grace period: Allow access for 7 days after payment failure
- ✅ Proration: Calculate based on days remaining in cycle
- ✅ Cancellation: Access until end of paid period

---

## Edge Cases & Error Handling

### License Assignment Edge Cases

**1. Concurrent Assignment**:
- **Problem**: Two admins assign last license simultaneously
- **Solution**: Use `SELECT ... FOR UPDATE` with row-level locking
- **Implementation**:
```sql
BEGIN TRANSACTION;
  SELECT available_count FROM tenant 
  WHERE id = tenant_id 
  FOR UPDATE;
  
  -- Check and update atomically
  IF available_count > 0 THEN
    UPDATE tenant SET ...;
  ELSE
    RAISE ERROR 'No available licenses';
  END IF;
COMMIT;
```

**2. User Already Has License**:
- **Problem**: Admin tries to assign license to user with active license
- **Solution**: 
  - Option A: Block assignment, require unassignment first
  - Option B: Auto-upgrade (unassign old, assign new)
- **Implementation**: Check `license_is_active` before assignment

**3. Pool Exhausted**:
- **Problem**: No available licenses in pool
- **Solution**: 
  - Show error message
  - Suggest upgrading pool (if super admin)
  - Suggest contacting support
- **UI**: Disable assignment button, show "Upgrade Pool" option

**4. Invalid Tier**:
- **Problem**: Tier doesn't exist or is inactive
- **Solution**: Validate tier before pool operations
- **Error**: "License tier not found or inactive"

### Credit Deduction Edge Cases

**1. Insufficient Credits**:
- **Problem**: User tries to use service but has no credits
- **Solution**: 
  - Block operation
  - Show credit balance
  - Suggest purchasing credits or upgrading tier
- **Implementation**: Check `credits_remaining > 0` before deduction

**2. Concurrent Deductions**:
- **Problem**: Multiple operations deduct credits simultaneously
- **Solution**: Atomic update with credit check
- **Implementation**:
```sql
UPDATE user SET
  credits_used = credits_used + deduction_amount,
  updated_at = NOW()
WHERE id = user_id 
  AND (credits_allocated - credits_used) >= deduction_amount;
```

**3. Negative Credits**:
- **Problem**: Credits go negative due to race condition
- **Solution**: Database constraint `CHECK (credits_used <= credits_allocated)`
- **Prevention**: Always check before deducting

**4. Expired License**:
- **Problem**: User's license expired but still has credits
- **Solution**: 
  - Check `license_expires_at` before operations
  - Deactivate license if expired
  - Allow credit usage until expiration (or block immediately)

### Pool Management Edge Cases

**1. Reducing Pool Below Assigned**:
- **Problem**: Super admin tries to reduce pool below assigned licenses
- **Solution**: Validate `new_total_count >= assigned_count`
- **Error**: "Cannot reduce pool below assigned licenses (X assigned)"

**2. Tier Deletion with Active Pools**:
- **Problem**: Super admin tries to delete tier with active pools
- **Solution**: 
  - Block deletion
  - Show list of tenants with pools
  - Require pool migration first
- **Error**: "Cannot delete tier: X tenants have active pools"

**3. Tenant Deletion with Active Licenses**:
- **Problem**: Super admin tries to delete tenant with assigned licenses
- **Solution**: 
  - Block deletion
  - Show list of users with licenses
  - Require license unassignment first
- **Error**: "Cannot delete tenant: X users have active licenses"

### Subscription Edge Cases

**1. Payment Failure**:
- **Problem**: Payment fails during renewal
- **Solution**: 
  - Mark subscription as `past_due`
  - Send notification to tenant admin
  - Allow grace period (7 days)
  - Cancel if payment fails after grace period

**2. Subscription Upgrade Mid-Cycle**:
- **Problem**: Tenant upgrades subscription mid-month
- **Solution**: 
  - Calculate prorated amount
  - Charge difference immediately
  - Update subscription immediately
  - Full amount charged on next renewal

**3. Subscription Downgrade**:
- **Problem**: Tenant downgrades but has more licenses than new tier allows
- **Solution**: 
  - Block downgrade if `assigned_count > new_tier_license_count`
  - Require unassignment of excess licenses first
  - Or: Allow downgrade, mark excess licenses as "grandfathered"

**4. Concurrent Renewals**:
- **Problem**: Renewal job runs multiple times
- **Solution**: Idempotent renewal check
- **Implementation**: Check `last_payment_date` before processing

---

## Frontend Views

### Super Admin Dashboard

**Main View**: `/admin/licenses`

**Sections**:

1. **License Tiers Management**
   - Table of all license tiers
   - Actions: Create, Edit, Delete, Activate/Deactivate
   - Columns: Name, Default Credits, Monthly Credits, Pricing, Limits, Status
   - Filters: Active/Inactive, Search by name

2. **Tenants & License Pools**
   - Table of all tenants
   - Expandable rows showing license pools per tier
   - Pool details: Total, Available, Assigned
   - Actions per tenant:
     - View pools
     - Add licenses to pool
     - Create new pool
     - View subscription status
   - Filters: Tenant name, Active/Inactive

3. **User Licenses Overview**
   - Table of all users with licenses
   - Columns: User, Tenant, Tier, Credits Allocated, Credits Used, Status
   - Actions: View details, Block/Unblock license
   - Filters: Tenant, Tier, Active/Inactive, Search by username

4. **Subscription Management**
   - Table of all subscriptions
   - Columns: Tenant, Tier, License Count, Amount, Status, Next Payment
   - Actions: View details, Cancel, Upgrade/Downgrade
   - Filters: Status, Tier, Search by tenant

5. **Analytics Dashboard**
   - Total licenses across all tenants
   - License utilization (assigned vs available)
   - Revenue metrics (subscription revenue)
   - Credit usage trends
   - Charts: License distribution, Revenue over time

**Key Features**:
- ✅ Bulk operations (assign licenses to multiple tenants)
- ✅ Export data (CSV, JSON)
- ✅ Audit log (all license operations)
- ✅ Payment history
- ✅ Subscription analytics

### Tenant Admin Dashboard

**Main View**: `/tenant/licenses`

**Sections**:

1. **License Pool Overview**
   - Cards showing pools by tier
   - Each card: Tier name, Total, Available, Assigned
   - Visual: Progress bars, color coding (green/yellow/red)
   - Quick actions: Assign license, Request more licenses

2. **User License Management**
   - Table of users in tenant
   - Columns: User, Tier, Credits Allocated, Credits Used, Credits Remaining, Status
   - Actions per user:
     - Assign license
     - Upgrade/Downgrade license
     - Unassign license
     - View credit history
   - Filters: Tier, Active/Inactive, Search by username
   - Bulk actions: Assign licenses to multiple users

3. **License Assignment Dialog**
   - Select user (dropdown or search)
   - Select tier (shows available count)
   - Preview: Credits user will receive
   - Confirm assignment
   - Success message with license details

4. **License Upgrade Dialog**
   - Current tier and credits
   - Select new tier
   - Preview changes:
     - New credits (if reset) or preserved credits
     - New monthly credits
     - Tier features comparison
   - Confirm upgrade
   - Success message

5. **Subscription & Billing**
   - Current subscription details:
     - Tier, License count, Monthly amount
     - Next payment date
     - Payment method
   - Actions:
     - Upgrade subscription
     - Downgrade subscription
     - Update payment method
     - Cancel subscription
   - Billing history table
   - Invoice downloads

6. **Credit Usage Dashboard**
   - Total credits across all users
   - Credits used this month
   - Top users by credit usage
   - Credit usage trends (chart)
   - Low credit warnings

**Key Features**:
- ✅ Real-time pool updates
- ✅ Credit balance notifications
- ✅ License expiration warnings
- ✅ Usage analytics
- ✅ Export reports

### User View (End User)

**Main View**: `/settings/credits`

**Sections**:

1. **Credit Balance**
   - Large display: Credits Remaining
   - Progress bar: Credits Used / Credits Allocated
   - Breakdown: Allocated, Used, Remaining
   - License tier badge

2. **Credit History**
   - Table of credit transactions
   - Columns: Date, Type, Amount, Balance Before, Balance After, Description
   - Filters: Date range, Transaction type
   - Export: Download CSV

3. **Usage Statistics**
   - Credits used this month
   - Average daily usage
   - Projected monthly usage
   - Low credit warning (if < 20% remaining)

**Key Features**:
- ✅ Real-time balance updates
- ✅ Transaction history
- ✅ Usage predictions
- ✅ Low credit alerts

---

## API Operations

### Super Admin APIs

**Base Path**: `/api/v2/admin/licenses`

**Endpoints**:

1. **License Tiers**
   - `GET /tiers` - List all tiers
   - `POST /tiers` - Create tier
   - `PUT /tiers/{tier_id}` - Update tier
   - `DELETE /tiers/{tier_id}` - Delete tier (if no pools)

2. **Tenant Pools**
   - `GET /tenants/{tenant_id}/pools` - Get tenant pools
   - `POST /tenants/{tenant_id}/pools` - Create pool
   - `PUT /tenants/{tenant_id}/pools/{tier_id}` - Update pool (add licenses)
   - `DELETE /tenants/{tenant_id}/pools/{tier_id}` - Delete pool (if no assignments)

3. **User Licenses**
   - `GET /user-licenses` - List all user licenses (filtered)
   - `PUT /user-licenses/{user_id}/block` - Block license
   - `PUT /user-licenses/{user_id}/unblock` - Unblock license

4. **Subscriptions**
   - `GET /subscriptions` - List all subscriptions
   - `POST /subscriptions` - Create subscription
   - `PUT /subscriptions/{subscription_id}` - Update subscription
   - `POST /subscriptions/{subscription_id}/cancel` - Cancel subscription

### Tenant Admin APIs

**Base Path**: `/api/v2/admin/licenses`

**Endpoints**:

1. **Pool Management**
   - `GET /tenant/pools` - Get tenant's pools
   - `POST /tenant/pools/request` - Request more licenses

2. **User License Assignment**
   - `GET /tenant/users/{user_id}/license` - Get user license
   - `POST /tenant/pools/{tier_id}/assign` - Assign license to user
   - `POST /tenant/users/{user_id}/unassign` - Unassign license
   - `POST /tenant/users/{user_id}/upgrade` - Upgrade user license
   - `POST /tenant/users/{user_id}/downgrade` - Downgrade user license

3. **Subscription**
   - `GET /tenant/subscription` - Get tenant subscription
   - `POST /tenant/subscription/upgrade` - Upgrade subscription
   - `POST /tenant/subscription/downgrade` - Downgrade subscription
   - `PUT /tenant/subscription/payment-method` - Update payment method

### User APIs

**Base Path**: `/api/v2/credits`

**Endpoints**:

1. **Credit Balance**
   - `GET /balance` - Get credit balance
   - `GET /transactions` - Get transaction history

---

## Summary

This business logic document covers:

✅ **Core Concepts**: Tiers, pools, user licenses
✅ **License Lifecycle**: Creation, assignment, management
✅ **Upgrades & Downgrades**: User and tenant level
✅ **Pool Management**: Adding licenses, creating pools
✅ **Payment Flow**: One-time and subscription payments
✅ **Subscription Model**: Monthly recurring, renewal, cancellation
✅ **Edge Cases**: Concurrent operations, errors, validations
✅ **Frontend Views**: Super admin, tenant admin, user views
✅ **API Operations**: Complete endpoint reference

All operations are designed to be:
- **Atomic**: Single transaction for related updates
- **Consistent**: Data integrity maintained
- **Auditable**: All changes logged
- **Scalable**: Handles 100+ concurrent users
- **User-friendly**: Clear error messages and workflows
