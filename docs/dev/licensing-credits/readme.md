# Licensing & Credits System Documentation

## Overview

This directory contains comprehensive documentation for the optimized licensing and credits system, designed for high concurrency (100+ concurrent users) and low latency.

## Documentation Structure

### Core Documents

1. **[complete_erd.md](./complete_erd.md)** - Complete Entity Relationship Diagram
   - Full table schemas with all fields
   - Relationships and constraints
   - SQL examples for key operations
   - Performance optimizations
   - Migration notes

2. **[new_architecture.md](./new_architecture.md)** - System Architecture
   - Architecture flow diagram
   - Super Admin vs Tenant Admin roles
   - License tier and pool management
   - User license assignment flow

3. **[business_logic.md](./business_logic.md)** - Complete Business Logic
   - License lifecycle and operations
   - Upgrades, downgrades, and edge cases
   - Payment and subscription flows
   - Frontend views (Super Admin, Tenant Admin, User)
   - API operations reference

## Quick Start

### For Developers

1. Start with [new_architecture.md](./new_architecture.md) to understand the system flow
2. Review [complete_erd.md](./complete_erd.md) for database schema details
3. Check the table relationships and constraints
4. Review SQL examples for common operations

### For Database Administrators

1. Review [complete_erd.md](./complete_erd.md) for complete schema
2. Check migration notes for schema changes
3. Review indexes for performance optimization
4. Understand concurrency considerations

## Key Design Principles

1. **Denormalization**: Store calculated values to avoid expensive joins
2. **Single Table Queries**: Merge related data into single tables where possible
3. **Atomic Updates**: All related updates happen in single transactions
4. **Separate Stats Tables**: Time-series data separated to avoid lock contention
5. **No Redundant Tables**: Removed unnecessary tables - everything merged efficiently

## System Overview

### Active Tables (8)

1. **`user`** - Users with merged license fields
2. **`license_tier`** - License tier definitions
3. **`tenant`** - Tenants with merged license pools (JSON) + subscription fields
4. **`subscription`** - Monthly subscription management
5. **`subscription_history`** - Subscription audit trail
6. **`transaction`** - Unified table for flow + credit transactions
7. **`tenant_usage_stats`** - Time-series statistics for tenants
8. **`user_usage_stats`** - Time-series statistics for users

### Removed Tables (4)

- `license` - Disabled (merged into user table)
- `user_license` - Disabled (merged into user table)
- `license_pool` - Disabled (merged into tenant as JSON)
- `credit_transaction` - Disabled (merged into transaction table)

## Architecture Flow

```
Super Admin
  ├─ Create License Tiers
  ├─ Create Tenants (with license pools)
  └─ Manage All Licenses

Tenant Admin
  ├─ View Tenant's License Pool
  ├─ Create Users
  └─ Assign Licenses to Users
```

## Key Features

- ✅ Single table queries for user + license
- ✅ License pools merged into tenant (no separate table)
- ✅ Denormalized counts in tenant.license_pools JSON
- ✅ Unified transaction table
- ✅ Separate stats tables for analytics
- ✅ Atomic updates for consistency
- ✅ Optimized indexes for performance
- ✅ Reduced table count (6 tables vs original 7+)

## Performance Optimizations

- **No Joins Needed**: User license data in single table
- **Denormalized Counts**: Pool counts stored directly (no COUNT queries)
- **JSON Storage**: License pools in tenant table (one query)
- **Indexed Foreign Keys**: Fast lookups and joins
- **Separate Stats**: No lock contention on main tables

## Concurrency Support

Designed for 100+ concurrent users with:
- Row-level locking for critical sections
- Atomic updates in single transactions
- Denormalized counts (no expensive COUNT queries)
- Separate stats tables (no lock contention)
- Optimized indexes for fast queries

---

For detailed information, see the individual documentation files listed above.
