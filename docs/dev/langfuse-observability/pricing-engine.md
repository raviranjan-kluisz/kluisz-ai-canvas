# Pricing Engine - Cost and Credits Calculation

## Overview

This document describes the Pricing Engine that converts costs from Langfuse traces to credits based on license tier pricing configurations. **Langfuse already calculates costs for each trace**, so we extract the cost directly and convert it to credits.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Langfuse Trace Data                             │
│  - Cost (already calculated by Langfuse)                    │
│  - Tokens (input, output, total)                            │
│  - Model information                                         │
│  - Trace metadata                                            │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Extract Cost
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          PricingEngine                                       │
│                                                               │
│  1. Extract Cost from Langfuse Trace for the particular user and tenant                      │
│     ├─ Get cost from trace.usage.totalCost                  │
│     ├─ Fallback to trace.cost or trace.totalCost            │
│     └─ Handle various cost field formats                     │
│                                                               │
│  2. Apply Tier Pricing Multiplier                           │
│     ├─ Get tier's pricing_multiplier                         │
│     ├─ Apply multiplier: cost * pricing_multiplier          │
│     └─ Handle discounts/bonuses                              │
│                                                               │
│  3. Convert Cost to Credits                                  │
│     ├─ Get tier's credits_per_usd                            │
│     ├─ Calculate credits = cost * credits_per_usd            │
│     └─ Round to nearest integer                              │
│                                                               │
│  4. Apply Tier-Specific Rules                                │
│     ├─ Check tier limits                                     │
│     ├─ Apply minimum/maximum credit rules                    │
│     └─ Handle special pricing                                │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Credits & Cost
                             │
┌────────────────────────────▼─────────────────────────────────┐
│          Usage Statistics                                    │
│  - tenant_usage_stats.total_cost_usd                        │
│  - tenant_usage_stats.total_credits_used                     │
│  - user_usage_stats.cost_usd                                │
│  - user_usage_stats.credits_used                             │
└───────────────────────────────────────────────────────────────┘
```

## Service Implementation

### Location

**File:** `src/backend/base/kluisz/services/pricing/engine.py`

### Core Class

```python
from decimal import Decimal
from klx.services.base import Service
from klx.services.settings.service import SettingsService
from klx.services.deps import session_scope

class PricingEngine(Service):
    """Pricing engine for converting Langfuse costs to credits."""
    
    name = "pricing_engine"
    
    def __init__(self, settings_service: SettingsService):
        self.settings_service = settings_service
```

## Cost Extraction Methods

### 1. Extract Cost from Langfuse Trace

```python
def extract_cost_from_trace(self, trace: dict) -> Decimal:
    """
    Extract cost from Langfuse trace.
    
    Langfuse provides cost in various locations:
    - trace.usage.totalCost (most common)
    - trace.usage.cost
    - trace.totalCost
    - trace.cost
    
    Args:
        trace: Langfuse trace dictionary
    
    Returns:
        Cost in USD (Decimal), defaults to 0.00 if not found
    """
    # Try to get usage object
    usage = (
        trace.get("usage") or 
        trace.get("totalUsage") or 
        {}
    )
    
    if not isinstance(usage, dict):
        usage = {}
    
    # Try various cost field locations
    cost_value = (
        usage.get("totalCost") or 
        usage.get("cost") or 
        usage.get("total_cost") or
        trace.get("totalCost") or
        trace.get("cost") or
        trace.get("total_cost") or
        0
    )
    
    # Convert to Decimal
    try:
        if isinstance(cost_value, (int, float)):
            cost = Decimal(str(cost_value))
        elif isinstance(cost_value, str):
            cost = Decimal(cost_value)
        else:
            cost = Decimal("0.00")
    except Exception:
        cost = Decimal("0.00")
    
    return cost
```

### 2. Apply Tier Pricing Multiplier

```python
async def apply_tier_multiplier(
    self,
    cost: Decimal,
    tier_id: UUIDstr | None = None,
) -> Decimal:
    """
    Apply tier-specific pricing multiplier to cost.
    
    Args:
        cost: Base cost from Langfuse
        tier_id: License tier ID (optional)
    
    Returns:
        Adjusted cost after applying multiplier
    """
    if not tier_id:
        return cost
    
    async with session_scope() as session:
        from kluisz.services.database.models.license_tier.model import LicenseTier
        tier = await session.get(LicenseTier, tier_id)
        
        if tier and tier.pricing_multiplier:
            # Apply multiplier (e.g., 0.95 = 5% discount, 1.00 = no change)
            cost = cost * tier.pricing_multiplier
    
    return cost.quantize(Decimal("0.01"))  # Round to 2 decimal places
```

### 3. Convert Cost to Credits

```python
async def calculate_credits_from_cost(
    self,
    cost_usd: Decimal,
    tier_id: UUIDstr,
) -> int:
    """
    Convert cost in USD to credits using tier's credits_per_usd.
    
    Process:
    1. Get tier's credits_per_usd
    2. Calculate credits = cost * credits_per_usd
    3. Round to nearest integer
    
    Args:
        cost_usd: Cost in USD (from Langfuse, after multiplier)
        tier_id: License tier ID (required)
    
    Returns:
        Credits (integer)
    """
    async with session_scope() as session:
        from kluisz.services.database.models.license_tier.model import LicenseTier
        tier = await session.get(LicenseTier, tier_id)
        
        if not tier:
            raise ValueError(f"License tier {tier_id} not found")
        
        credits_per_usd = tier.credits_per_usd or Decimal("0.00")
    
    # Convert cost to credits
    credits = cost_usd * credits_per_usd
    
    return int(credits.quantize(Decimal("1")))  # Round to nearest integer
```

### 4. Process Trace (Complete Flow)

```python
async def process_trace_for_credits(
    self,
    trace: dict,
    tier_id: UUIDstr,
) -> tuple[Decimal, int]:
    """
    Process a Langfuse trace to get cost and credits.
    
    Complete flow:
    1. Extract cost from trace
    2. Apply tier pricing multiplier
    3. Convert to credits
    
    Args:
        trace: Langfuse trace dictionary
        tier_id: License tier ID
    
    Returns:
        Tuple of (cost_usd, credits)
    """
    # Step 1: Extract cost from Langfuse trace
    cost = self.extract_cost_from_trace(trace)
    
    # Step 2: Apply tier pricing multiplier
    cost = await self.apply_tier_multiplier(cost, tier_id)
    
    # Step 3: Convert to credits
    credits = await self.calculate_credits_from_cost(cost, tier_id)
    
    return cost, credits
```

## License Tier Pricing Configuration

### Tier Model Fields

**Model:** `LicenseTier`

```python
class LicenseTier(SQLModel, table=True):
    # Pricing
    credits_per_usd: Decimal = Decimal("0.00")       # Credits per USD
    pricing_multiplier: Decimal = Decimal("1.00")     # Cost multiplier
    
    # Example configurations:
    # Starter tier: credits_per_usd = 100 (100 credits per $1)
    # Pro tier: credits_per_usd = 200 (200 credits per $1)
    # Enterprise tier: credits_per_usd = 500 (500 credits per $1)
    
    # pricing_multiplier examples:
    # 1.00 = no change (standard pricing)
    # 0.95 = 5% discount
    # 0.90 = 10% discount
    # 1.10 = 10% markup
```

### Example Tier Configurations

```python
# Starter Tier
{
    "name": "Starter",
    "credits_per_usd": Decimal("100.00"),  # 100 credits per $1
    "pricing_multiplier": Decimal("1.00"),  # No multiplier (standard pricing)
    "default_credits": 1000,
}

# Professional Tier
{
    "name": "Professional",
    "credits_per_usd": Decimal("200.00"),  # 200 credits per $1
    "pricing_multiplier": Decimal("0.95"),  # 5% discount
    "default_credits": 10000,
}

# Enterprise Tier
{
    "name": "Enterprise",
    "credits_per_usd": Decimal("500.00"),  # 500 credits per $1
    "pricing_multiplier": Decimal("0.90"),  # 10% discount
    "default_credits": 100000,
}
```

## Usage Examples

### Example 1: Extract Cost from Trace

```python
# Trace data from Langfuse
trace = {
    "usage": {
        "inputTokens": 1000,
        "outputTokens": 500,
        "totalCost": 0.06,  # Langfuse already calculated this!
    },
    "metadata": {
        "model": "gpt-4",
    },
}

# Extract cost
pricing_engine = PricingEngine(settings_service)
cost = pricing_engine.extract_cost_from_trace(trace)

# Result: $0.06 (directly from Langfuse)
```

### Example 2: Process Trace for Credits

```python
# Process trace for credits
cost, credits = await pricing_engine.process_trace_for_credits(
    trace=trace,
    tier_id=user.license_tier_id,  # Professional tier
)

# Process:
# 1. Extract cost = $0.06 (from Langfuse)
# 2. Apply tier multiplier (0.95) = $0.057
# 3. Convert to credits = $0.057 * 200 credits/USD = 11.4 credits
# 4. Round to 11 credits
# 
# Result: cost = $0.057, credits = 11
```

### Example 3: Batch Processing Traces

```python
# Process multiple traces
traces = await langfuse_client.get_traces(...)

total_cost = Decimal("0.00")
total_credits = 0

for trace in traces:
    # Process each trace
    cost, credits = await pricing_engine.process_trace_for_credits(
        trace=trace,
        tier_id=user.license_tier_id,
    )
    
    total_cost += cost
    total_credits += credits

# Update usage stats
stats.total_cost_usd = total_cost
stats.total_credits_used = total_credits
```

## Integration with Analytics Service

The pricing engine is used by the analytics service:

```python
# In analytics_service.py
from kluisz.services.pricing.engine import PricingEngine

pricing_engine = PricingEngine(self.settings_service)

# For each trace:
# 1. Extract cost from Langfuse trace
cost = pricing_engine.extract_cost_from_trace(trace)

# 2. Apply tier multiplier
cost = await pricing_engine.apply_tier_multiplier(
    cost=cost,
    tier_id=user.license_tier_id,
)

# 3. Convert to credits
credits = await pricing_engine.calculate_credits_from_cost(
    cost_usd=cost,
    tier_id=user.license_tier_id,
)

# Aggregate
total_cost += cost
total_credits += credits
```

## Cost Breakdown

### By Model

```python
async def get_cost_breakdown_by_model(
    self,
    traces: list[dict],
    tier_id: UUIDstr,
) -> dict[str, Decimal]:
    """Get cost breakdown by model."""
    breakdown = {}
    
    for trace in traces:
        model = trace.get("metadata", {}).get("model", "unknown")
        
        # Extract cost from trace
        cost = self.extract_cost_from_trace(trace)
        
        # Apply tier multiplier
        cost = await self.apply_tier_multiplier(cost, tier_id)
        
        breakdown[model] = breakdown.get(model, Decimal("0.00")) + cost
    
    return breakdown
```

### By User

```python
async def get_cost_breakdown_by_user(
    self,
    traces: list[dict],
    tier_id: UUIDstr,
) -> dict[str, Decimal]:
    """Get cost breakdown by user."""
    breakdown = {}
    
    for trace in traces:
        user_id = trace.get("user_id", "unknown")
        
        # Extract cost from trace
        cost = self.extract_cost_from_trace(trace)
        
        # Apply tier multiplier
        cost = await self.apply_tier_multiplier(cost, tier_id)
        
        breakdown[user_id] = breakdown.get(user_id, Decimal("0.00")) + cost
    
    return breakdown
```

## Tier-Specific Rules

### Minimum Credits

```python
async def apply_minimum_credits(
    self,
    credits: int,
    tier_id: UUIDstr,
) -> int:
    """Apply minimum credits rule for tier."""
    async with session_scope() as session:
        from kluisz.services.database.models.license_tier.model import LicenseTier
        tier = await session.get(LicenseTier, tier_id)
        
        if tier and tier.features.get("minimum_credits_per_trace"):
            min_credits = tier.features["minimum_credits_per_trace"]
            credits = max(credits, min_credits)
    
    return credits
```

### Maximum Credits

```python
async def apply_maximum_credits(
    self,
    credits: int,
    tier_id: UUIDstr,
) -> int:
    """Apply maximum credits rule for tier."""
    async with session_scope() as session:
        from kluisz.services.database.models.license_tier.model import LicenseTier
        tier = await session.get(LicenseTier, tier_id)
        
        if tier and tier.features.get("maximum_credits_per_trace"):
            max_credits = tier.features["maximum_credits_per_trace"]
            credits = min(credits, max_credits)
    
    return credits
```

## Error Handling

```python
def extract_cost_from_trace(self, trace: dict) -> Decimal:
    """Extract cost with error handling."""
    try:
        usage = trace.get("usage") or trace.get("totalUsage") or {}
        if not isinstance(usage, dict):
            usage = {}
        
        cost_value = (
            usage.get("totalCost") or 
            usage.get("cost") or 
            trace.get("totalCost") or
            trace.get("cost") or
            0
        )
        
        if isinstance(cost_value, (int, float)):
            return Decimal(str(cost_value))
        elif isinstance(cost_value, str):
            return Decimal(cost_value)
        else:
            return Decimal("0.00")
    
    except Exception as e:
        logger.error(f"Error extracting cost from trace: {e}")
        # Return zero cost on error (don't break analytics)
        return Decimal("0.00")
```

## Langfuse Cost Field Locations

Langfuse provides cost in various locations in the trace object:

1. **Primary location**: `trace.usage.totalCost` (most common)
2. **Alternative locations**:
   - `trace.usage.cost`
   - `trace.usage.total_cost`
   - `trace.totalCost`
   - `trace.cost`
   - `trace.total_cost`

The pricing engine handles all these locations and falls back to `0.00` if cost is not found.

## Benefits of Using Langfuse Costs

1. **Accuracy**: Langfuse calculates costs using actual model pricing
2. **Up-to-date**: Langfuse maintains current pricing for all models
3. **Simplicity**: No need to maintain model pricing tables
4. **Reliability**: Langfuse handles pricing updates automatically
5. **Consistency**: Same cost calculation across all traces

## Next Steps

1. **Analytics Service**: See [analytics-service.md](./analytics-service.md) for usage statistics updates
2. **Frontend Dashboards**: See [frontend-dashboards-plan.md](./frontend-dashboards-plan.md) for cost display
3. **API Endpoints**: See [readme.md](./readme.md) for pricing API reference
