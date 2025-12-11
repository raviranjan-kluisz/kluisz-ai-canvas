"""Pricing Engine for converting Langfuse costs to credits.

Langfuse already calculates costs for each trace. This engine:
1. Extracts cost from Langfuse trace data
2. Applies tier-specific pricing multipliers
3. Converts cost to credits based on tier configuration
"""

from decimal import Decimal
from typing import Any

from klx.log.logger import logger
from klx.services.deps import session_scope

from kluisz.schema.serialize import UUIDstr, str_to_uuid
from kluisz.services.base import Service


class PricingEngine(Service):
    """Pricing engine for converting Langfuse costs to credits.
    
    Langfuse provides cost directly in trace data. This engine:
    - Extracts cost from traces
    - Applies tier-specific multipliers (discounts/markups)
    - Converts cost to credits using tier's credits_per_usd
    """

    name = "pricing_engine"

    def extract_cost_from_trace(self, trace: dict[str, Any]) -> Decimal:
        """Extract cost from Langfuse trace.
        
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
        try:
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
            if isinstance(cost_value, (int, float)):
                return Decimal(str(cost_value))
            elif isinstance(cost_value, str):
                return Decimal(cost_value)
            elif isinstance(cost_value, Decimal):
                return cost_value
            else:
                return Decimal("0.00")
                
        except Exception as e:
            logger.error(f"Error extracting cost from trace: {e}")
            return Decimal("0.00")

    def extract_tokens_from_trace(self, trace: dict[str, Any]) -> dict[str, int]:
        """Extract token counts from Langfuse trace.
        
        Args:
            trace: Langfuse trace dictionary
        
        Returns:
            Dictionary with input_tokens, output_tokens, total_tokens
        """
        try:
            usage = trace.get("usage") or trace.get("totalUsage") or {}
            
            if not isinstance(usage, dict):
                usage = {}
            
            return {
                "input_tokens": usage.get("inputTokens", 0) or usage.get("input_tokens", 0) or 0,
                "output_tokens": usage.get("outputTokens", 0) or usage.get("output_tokens", 0) or 0,
                "total_tokens": usage.get("totalTokens", 0) or usage.get("total_tokens", 0) or 0,
            }
            
        except Exception as e:
            logger.error(f"Error extracting tokens from trace: {e}")
            return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    async def apply_tier_multiplier(
        self,
        cost: Decimal,
        tier_id: UUIDstr | None = None,
    ) -> Decimal:
        """Apply tier-specific pricing multiplier to cost.
        
        Tiers can have:
        - pricing_multiplier = 1.00 (standard, no change)
        - pricing_multiplier = 0.95 (5% discount)
        - pricing_multiplier = 0.90 (10% discount)
        - pricing_multiplier = 1.10 (10% markup)
        
        Args:
            cost: Base cost from Langfuse
            tier_id: License tier ID (optional)
        
        Returns:
            Adjusted cost after applying multiplier
        """
        if not tier_id:
            return cost
        
        try:
            async with session_scope() as session:
                from kluisz.services.database.models.license_tier.model import LicenseTier
                tier = await session.get(LicenseTier, str_to_uuid(tier_id))
                
                if tier and tier.pricing_multiplier:
                    # Apply multiplier
                    multiplier = Decimal(str(tier.pricing_multiplier))
                    cost = cost * multiplier
            
            # Round to 2 decimal places
            return cost.quantize(Decimal("0.01"))
            
        except Exception as e:
            logger.error(f"Error applying tier multiplier: {e}")
            return cost

    async def calculate_credits_from_cost(
        self,
        cost_usd: Decimal,
        tier_id: UUIDstr,
    ) -> int:
        """Convert cost in USD to credits using tier's credits_per_usd.
        
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
        try:
            async with session_scope() as session:
                from kluisz.services.database.models.license_tier.model import LicenseTier
                tier = await session.get(LicenseTier, str_to_uuid(tier_id))
                
                if not tier:
                    raise ValueError(f"License tier {tier_id} not found")
                
                credits_per_usd = Decimal(str(tier.credits_per_usd or 0))
            
            # Convert cost to credits
            credits = cost_usd * credits_per_usd
            
            # Round to nearest integer
            return int(credits.quantize(Decimal("1")))
            
        except Exception as e:
            logger.error(f"Error calculating credits from cost: {e}")
            raise

    async def process_trace_for_credits(
        self,
        trace: dict[str, Any],
        tier_id: UUIDstr,
    ) -> tuple[Decimal, int]:
        """Process a Langfuse trace to get cost and credits.
        
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

    async def process_traces_batch(
        self,
        traces: list[dict[str, Any]],
        tier_id: UUIDstr,
    ) -> dict[str, Any]:
        """Process multiple traces and get aggregated costs and credits.
        
        Args:
            traces: List of Langfuse trace dictionaries
            tier_id: License tier ID
        
        Returns:
            Dictionary with total_cost_usd, total_credits, trace_count
        """
        total_cost = Decimal("0.00")
        total_credits = 0
        total_tokens = 0
        
        for trace in traces:
            cost, credits = await self.process_trace_for_credits(trace, tier_id)
            total_cost += cost
            total_credits += credits
            
            tokens = self.extract_tokens_from_trace(trace)
            total_tokens += tokens["total_tokens"]
        
        return {
            "total_cost_usd": float(total_cost),
            "total_credits": total_credits,
            "total_tokens": total_tokens,
            "trace_count": len(traces),
        }

    async def apply_minimum_credits(
        self,
        credits: int,
        tier_id: UUIDstr,
    ) -> int:
        """Apply minimum credits rule for tier.
        
        Some tiers may have a minimum credits per trace rule.
        
        Args:
            credits: Calculated credits
            tier_id: License tier ID
        
        Returns:
            Credits (at least minimum)
        """
        try:
            async with session_scope() as session:
                from kluisz.services.database.models.license_tier.model import LicenseTier
                tier = await session.get(LicenseTier, str_to_uuid(tier_id))
                
                if tier and tier.features:
                    features = tier.features or {}
                    min_credits = features.get("minimum_credits_per_trace")
                    if min_credits:
                        credits = max(credits, int(min_credits))
            
            return credits
            
        except Exception as e:
            logger.error(f"Error applying minimum credits: {e}")
            return credits

    async def apply_maximum_credits(
        self,
        credits: int,
        tier_id: UUIDstr,
    ) -> int:
        """Apply maximum credits rule for tier.
        
        Some tiers may have a maximum credits per trace rule.
        
        Args:
            credits: Calculated credits
            tier_id: License tier ID
        
        Returns:
            Credits (at most maximum)
        """
        try:
            async with session_scope() as session:
                from kluisz.services.database.models.license_tier.model import LicenseTier
                tier = await session.get(LicenseTier, str_to_uuid(tier_id))
                
                if tier and tier.features:
                    features = tier.features or {}
                    max_credits = features.get("maximum_credits_per_trace")
                    if max_credits:
                        credits = min(credits, int(max_credits))
            
            return credits
            
        except Exception as e:
            logger.error(f"Error applying maximum credits: {e}")
            return credits

    async def get_cost_breakdown_by_model(
        self,
        traces: list[dict[str, Any]],
        tier_id: UUIDstr,
    ) -> dict[str, dict[str, Any]]:
        """Get cost breakdown by model.
        
        Args:
            traces: List of Langfuse trace dictionaries
            tier_id: License tier ID
        
        Returns:
            Dictionary mapping model name to cost/credits
        """
        breakdown: dict[str, dict[str, Any]] = {}
        
        for trace in traces:
            metadata = trace.get("metadata", {})
            model = metadata.get("model", "unknown")
            
            # Extract and process cost
            cost = self.extract_cost_from_trace(trace)
            cost = await self.apply_tier_multiplier(cost, tier_id)
            credits = await self.calculate_credits_from_cost(cost, tier_id)
            
            tokens = self.extract_tokens_from_trace(trace)
            
            if model not in breakdown:
                breakdown[model] = {
                    "total_cost_usd": Decimal("0.00"),
                    "total_credits": 0,
                    "total_tokens": 0,
                    "trace_count": 0,
                }
            
            breakdown[model]["total_cost_usd"] += cost
            breakdown[model]["total_credits"] += credits
            breakdown[model]["total_tokens"] += tokens["total_tokens"]
            breakdown[model]["trace_count"] += 1
        
        # Convert Decimal to float for JSON serialization
        for model_data in breakdown.values():
            model_data["total_cost_usd"] = float(model_data["total_cost_usd"])
        
        return breakdown

    async def get_cost_breakdown_by_user(
        self,
        traces: list[dict[str, Any]],
        tier_id: UUIDstr,
    ) -> dict[str, dict[str, Any]]:
        """Get cost breakdown by user.
        
        Args:
            traces: List of Langfuse trace dictionaries
            tier_id: License tier ID
        
        Returns:
            Dictionary mapping user_id to cost/credits
        """
        breakdown: dict[str, dict[str, Any]] = {}
        
        for trace in traces:
            user_id = trace.get("user_id", "unknown")
            
            # Extract and process cost
            cost = self.extract_cost_from_trace(trace)
            cost = await self.apply_tier_multiplier(cost, tier_id)
            credits = await self.calculate_credits_from_cost(cost, tier_id)
            
            tokens = self.extract_tokens_from_trace(trace)
            
            if user_id not in breakdown:
                breakdown[user_id] = {
                    "total_cost_usd": Decimal("0.00"),
                    "total_credits": 0,
                    "total_tokens": 0,
                    "trace_count": 0,
                }
            
            breakdown[user_id]["total_cost_usd"] += cost
            breakdown[user_id]["total_credits"] += credits
            breakdown[user_id]["total_tokens"] += tokens["total_tokens"]
            breakdown[user_id]["trace_count"] += 1
        
        # Convert Decimal to float for JSON serialization
        for user_data in breakdown.values():
            user_data["total_cost_usd"] = float(user_data["total_cost_usd"])
        
        return breakdown

    async def estimate_credits_for_tokens(
        self,
        tokens: int,
        model: str,
        tier_id: UUIDstr,
    ) -> int:
        """Estimate credits for a given number of tokens.
        
        Uses approximate pricing for common models.
        
        Args:
            tokens: Number of tokens
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            tier_id: License tier ID
        
        Returns:
            Estimated credits
        """
        # Approximate cost per 1K tokens for common models
        model_pricing = {
            "gpt-4": Decimal("0.06"),
            "gpt-4-turbo": Decimal("0.03"),
            "gpt-4o": Decimal("0.01"),
            "gpt-4o-mini": Decimal("0.0003"),
            "gpt-3.5-turbo": Decimal("0.002"),
            "claude-3-opus": Decimal("0.075"),
            "claude-3-sonnet": Decimal("0.015"),
            "claude-3-haiku": Decimal("0.00125"),
            "claude-3.5-sonnet": Decimal("0.015"),
            "default": Decimal("0.01"),
        }
        
        # Get price per 1K tokens
        price_per_1k = model_pricing.get(model.lower(), model_pricing["default"])
        
        # Calculate cost
        cost = (Decimal(str(tokens)) / 1000) * price_per_1k
        
        # Apply tier multiplier and convert to credits
        cost = await self.apply_tier_multiplier(cost, tier_id)
        credits = await self.calculate_credits_from_cost(cost, tier_id)
        
        return credits

    async def teardown(self) -> None:
        """Cleanup resources."""
        pass

