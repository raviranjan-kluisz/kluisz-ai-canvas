"""Lightweight metering callback for local billing - captures LLM usage in real-time.

This callback fires alongside Langfuse but stores data locally for immediate 
credit deduction. No external API calls, just local DB writes.

Benefits:
- Real-time billing (no waiting for Langfuse to process traces)
- No API rate limits or pagination issues
- Fast analytics queries (local DB vs external API)
- Reliable (no external dependencies for billing)

Pricing Configuration:
- All model pricing is controlled via: src/backend/base/kluisz/config/pricing.json
- Format: {"model_pricing": {"model-name": [input_price, output_price]}}
- Prices are per 1K tokens
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from klx.log.logger import logger

# Config file path - this is THE source of truth for pricing
PRICING_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "pricing.json"


def _load_pricing_config() -> dict[str, tuple[float, float]]:
    """Load pricing from config file: src/backend/base/kluisz/config/pricing.json
    
    Returns:
        Dict mapping model name prefix to (input_price, output_price) per 1K tokens
    """
    pricing: dict[str, tuple[float, float]] = {}
    
    if not PRICING_CONFIG_PATH.exists():
        logger.error(f"Pricing config not found: {PRICING_CONFIG_PATH}")
        # Fallback default
        return {"default": (0.002, 0.006)}
    
    try:
        with open(PRICING_CONFIG_PATH) as f:
            config = json.load(f)
        
        if "model_pricing" in config and isinstance(config["model_pricing"], dict):
            for model_key, prices in config["model_pricing"].items():
                if isinstance(prices, (list, tuple)) and len(prices) >= 2:
                    pricing[model_key] = (float(prices[0]), float(prices[1]))
        
        logger.debug(f"Loaded {len(pricing)} pricing entries from {PRICING_CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to load pricing config: {e}")
        return {"default": (0.002, 0.006)}
    
    return pricing


class KluiszMeteringCallback(AsyncCallbackHandler):
    """Captures LLM usage for local billing in real-time.
    
    This callback is added to the Langchain callback chain alongside
    Langfuse. When an LLM call completes:
    - Langfuse: sends detailed trace to cloud (for observability)
    - This callback: stores usage locally (for billing)
    
    At the end of the trace, `finalize_and_deduct()` is called to
    deduct credits based on accumulated usage.
    
    Pricing Configuration:
    - Default pricing is in DEFAULT_MODEL_PRICING (module level)
    - Can be overridden via: {KLUISZ_CONFIG_DIR}/pricing_config.json
    - Config is loaded once at class initialization
    """
    
    # Loaded from config file + defaults (initialized lazily)
    _model_pricing: dict[str, tuple[float, float]] | None = None
    
    @classmethod
    def get_model_pricing(cls) -> dict[str, tuple[float, float]]:
        """Get model pricing, loading from config if not already loaded."""
        if cls._model_pricing is None:
            cls._model_pricing = _load_pricing_config()
        return cls._model_pricing
    
    @classmethod
    def reload_pricing(cls) -> dict[str, tuple[float, float]]:
        """Force reload pricing from config file."""
        cls._model_pricing = _load_pricing_config()
        return cls._model_pricing
    
    def __init__(
        self,
        user_id: str,
        tenant_id: str | None = None,
        flow_id: str | None = None,
        trace_id: str | None = None,
    ):
        """Initialize the metering callback.
        
        Args:
            user_id: The user executing the flow
            tenant_id: The tenant context (optional, fetched from user if not provided)
            flow_id: The flow being executed
            trace_id: Unique trace identifier for correlation
        """
        super().__init__()
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.flow_id = flow_id
        self.trace_id = trace_id
        
        # Accumulated usage for this trace
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_tokens = 0
        self._total_cost = Decimal("0.00")
        self._llm_calls: list[dict[str, Any]] = []
    
    @property
    def ignore_chain(self) -> bool:
        """Don't ignore chain callbacks."""
        return False
    
    @property
    def ignore_llm(self) -> bool:
        """Don't ignore LLM callbacks - we need these!"""
        return False
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called after each LLM call completes - capture usage immediately.
        
        Priority: Extract cost from response FIRST (if provided by OpenAI/SDK),
        then fall back to pricing table estimates.
        
        This is where we extract token counts and cost from the LLM response.
        The data is accumulated and stored locally at the end of the trace.
        """
        try:
            print(f"\n{'='*60}")
            print(f"[METERING] on_llm_end called for user={self.user_id[:8] if self.user_id else 'None'}...")
            llm_output = response.llm_output or {}
            print(f"[METERING] LLM output keys: {list(llm_output.keys()) if llm_output else 'empty'}")
            print(f"[METERING] Full llm_output: {llm_output}")
            
            # Debug: Check generations structure
            if hasattr(response, 'generations') and response.generations:
                for i, gen_list in enumerate(response.generations):
                    for j, gen in enumerate(gen_list):
                        print(f"[METERING] Generation[{i}][{j}] type: {type(gen).__name__}")
                        if hasattr(gen, 'generation_info'):
                            print(f"[METERING] generation_info: {gen.generation_info}")
                        if hasattr(gen, 'message'):
                            msg = gen.message
                            print(f"[METERING] message type: {type(msg).__name__}")
                            if hasattr(msg, 'response_metadata'):
                                print(f"[METERING] response_metadata: {msg.response_metadata}")
                            if hasattr(msg, 'usage_metadata'):
                                print(f"[METERING] usage_metadata: {msg.usage_metadata}")
            
            # Try to get usage from llm_output first
            token_usage = (
                llm_output.get("token_usage") or 
                llm_output.get("usage") or
                {}
            )
            
            # Also try to get from response metadata (OpenAI style)
            if not token_usage and hasattr(response, 'generations') and response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        if hasattr(gen, 'generation_info') and gen.generation_info:
                            gen_info = gen.generation_info
                            if 'usage' in gen_info:
                                token_usage = gen_info['usage']
                                print(f"[METERING] Found usage in generation_info: {token_usage}")
                                break
                            if 'token_usage' in gen_info:
                                token_usage = gen_info['token_usage']
                                print(f"[METERING] Found token_usage in generation_info: {token_usage}")
                                break
                        # Check message response_metadata for usage
                        if hasattr(gen, 'message'):
                            msg = gen.message
                            # Try response_metadata first
                            if hasattr(msg, 'response_metadata') and msg.response_metadata:
                                meta = msg.response_metadata
                                if 'token_usage' in meta:
                                    token_usage = meta['token_usage']
                                    print(f"[METERING] Found token_usage in response_metadata: {token_usage}")
                                    break
                                if 'usage' in meta:
                                    token_usage = meta['usage']
                                    print(f"[METERING] Found usage in response_metadata: {token_usage}")
                                    break
                            # Try usage_metadata (newer Langchain format)
                            if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                                um = msg.usage_metadata
                                # usage_metadata is a dict-like object
                                if hasattr(um, 'input_tokens') or isinstance(um, dict):
                                    token_usage = {
                                        'prompt_tokens': getattr(um, 'input_tokens', 0) or um.get('input_tokens', 0),
                                        'completion_tokens': getattr(um, 'output_tokens', 0) or um.get('output_tokens', 0),
                                        'total_tokens': getattr(um, 'total_tokens', 0) or um.get('total_tokens', 0),
                                    }
                                    print(f"[METERING] Found usage in usage_metadata: {token_usage}")
                                    break
            
            print(f"[METERING] Token usage extracted: {token_usage}")
            
            input_tokens = (
                token_usage.get("prompt_tokens") or 
                token_usage.get("input_tokens") or 
                0
            )
            output_tokens = (
                token_usage.get("completion_tokens") or 
                token_usage.get("output_tokens") or 
                0
            )
            total_tokens = (
                token_usage.get("total_tokens") or 
                (input_tokens + output_tokens)
            )
            
            print(f"[METERING] Tokens: input={input_tokens}, output={output_tokens}, total={total_tokens}")
            
            # Extract model info - check multiple sources
            model = (
                llm_output.get("model_name") or 
                llm_output.get("model") or 
                token_usage.get("model") or
                "unknown"
            )
            
            # Also check response_metadata from message (OpenAI style)
            if model == "unknown" and hasattr(response, 'generations') and response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        if hasattr(gen, 'message'):
                            msg = gen.message
                            # Check response_metadata for model_name
                            if hasattr(msg, 'response_metadata') and msg.response_metadata:
                                meta = msg.response_metadata
                                if 'model_name' in meta:
                                    model = meta['model_name']
                                    print(f"[METERING] Found model_name in response_metadata: {model}")
                                    break
                                if 'model' in meta:
                                    model = meta['model']
                                    print(f"[METERING] Found model in response_metadata: {model}")
                                    break
                            # Also check generation_info
                            if hasattr(gen, 'generation_info') and gen.generation_info:
                                gen_info = gen.generation_info
                                if 'model_name' in gen_info:
                                    model = gen_info['model_name']
                                    print(f"[METERING] Found model_name in generation_info: {model}")
                                    break
                                if 'model' in gen_info:
                                    model = gen_info['model']
                                    print(f"[METERING] Found model in generation_info: {model}")
                                    break
                        if model != "unknown":
                            break
                    if model != "unknown":
                        break
            
            # PRIORITY 1: Extract cost from OpenAI response (HIGHEST PRIORITY)
            # Check ALL possible locations where cost might be provided
            # This includes response_metadata, usage_metadata, generation_info, etc.
            cost_from_response = self._extract_cost_from_response(response, llm_output, token_usage)
            
            # Also check kwargs (sometimes cost is passed through kwargs)
            if cost_from_response is None and kwargs:
                cost_from_kwargs = (
                    kwargs.get('cost') or
                    kwargs.get('total_cost') or
                    kwargs.get('usage_cost')
                )
                if cost_from_kwargs is not None:
                    cost_from_response = Decimal(str(cost_from_kwargs))
                    print(f"[METERING] ✅ Found cost in kwargs: ${cost_from_response}")
            
            # Calculate cost (use response cost if available, otherwise estimate)
            if cost_from_response is not None:
                cost = cost_from_response
                print(f"[METERING] ✅ Using cost from OpenAI response: ${cost}")
            else:
                cost = self._calculate_cost(llm_output, model, input_tokens, output_tokens)
                print(f"[METERING] ⚠️ No cost in response, estimated using pricing table: ${cost} (model: {model})")
            
            # Accumulate for this trace
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_tokens += total_tokens
            self._total_cost += cost
            
            # Store individual call info for detailed breakdown
            self._llm_calls.append({
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": float(cost),
            })
            
            logger.debug(
                f"Metering: {model} - {total_tokens} tokens, ${cost:.6f} "
                f"(user={self.user_id[:8]}..., tenant={self.tenant_id[:8] if self.tenant_id else 'N/A'}...)"
            )
            
        except Exception as e:
            logger.warning(f"Error in metering callback on_llm_end: {e}")
    
    def _extract_cost_from_response(
        self,
        response: LLMResult,
        llm_output: dict,
        token_usage: dict,
    ) -> Decimal | None:
        """Extract cost from OpenAI response - checks ALL possible locations.
        
        OpenAI's API doesn't directly return cost, but some SDKs/wrappers calculate it.
        We check all possible locations where cost might be provided.
        
        Priority order (checked in sequence):
        1. response_metadata (OpenAI SDK sometimes calculates and includes here)
        2. usage_metadata (Langchain's usage metadata)
        3. generation_info (generation-level metadata)
        4. llm_output dict (top-level response dict)
        5. token_usage dict (usage object)
        6. Nested usage objects
        
        Returns:
            Cost as Decimal if found, None otherwise
        """
        cost = None
        
        # Check 1: response_metadata (OpenAI SDK sometimes calculates cost here)
        if hasattr(response, 'generations') and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    # Check message.response_metadata (most common location)
                    if hasattr(gen, 'message') and hasattr(gen.message, 'response_metadata'):
                        meta = gen.message.response_metadata
                        if isinstance(meta, dict):
                            # Try various cost field names (different SDKs use different names)
                            cost = (
                                meta.get('cost') or
                                meta.get('total_cost') or
                                meta.get('usage_cost') or
                                meta.get('billing_cost') or
                                meta.get('price') or
                                meta.get('total_price')
                            )
                            if cost is not None:
                                print(f"[METERING] ✅ Found cost in response_metadata: ${cost}")
                                return Decimal(str(cost))
                    
                    # Check message.usage_metadata (Langchain's usage metadata object)
                    if hasattr(gen, 'message') and hasattr(gen.message, 'usage_metadata'):
                        um = gen.message.usage_metadata
                        # usage_metadata can be a dict or an object with attributes
                        if isinstance(um, dict):
                            cost = (
                                um.get('cost') or
                                um.get('total_cost') or
                                um.get('usage_cost')
                            )
                        else:
                            # Try as object attributes
                            cost = (
                                getattr(um, 'cost', None) or
                                getattr(um, 'total_cost', None) or
                                getattr(um, 'usage_cost', None)
                            )
                        if cost is not None:
                            print(f"[METERING] ✅ Found cost in usage_metadata: ${cost}")
                            return Decimal(str(cost))
                    
                    # Check generation_info (generation-level metadata)
                    if hasattr(gen, 'generation_info') and gen.generation_info:
                        gen_info = gen.generation_info
                        if isinstance(gen_info, dict):
                            cost = (
                                gen_info.get('cost') or
                                gen_info.get('total_cost') or
                                gen_info.get('usage_cost') or
                                gen_info.get('price')
                            )
                            if cost is not None:
                                print(f"[METERING] ✅ Found cost in generation_info: ${cost}")
                                return Decimal(str(cost))
        
        # Check 2: llm_output dict (top-level response dict)
        if isinstance(llm_output, dict):
            cost = (
                llm_output.get('cost') or
                llm_output.get('total_cost') or
                llm_output.get('usage_cost') or
                llm_output.get('price') or
                llm_output.get('total_price')
            )
            if cost is not None:
                print(f"[METERING] ✅ Found cost in llm_output: ${cost}")
                return Decimal(str(cost))
        
        # Check 3: token_usage dict (usage object passed in)
        if isinstance(token_usage, dict):
            cost = (
                token_usage.get('cost') or
                token_usage.get('total_cost') or
                token_usage.get('usage_cost') or
                token_usage.get('price')
            )
            if cost is not None:
                print(f"[METERING] ✅ Found cost in token_usage: ${cost}")
                return Decimal(str(cost))
        
        # Check 4: Nested usage objects in llm_output
        usage_in_llm = llm_output.get('token_usage') or llm_output.get('usage')
        if isinstance(usage_in_llm, dict):
            cost = (
                usage_in_llm.get('cost') or
                usage_in_llm.get('total_cost') or
                usage_in_llm.get('usage_cost') or
                usage_in_llm.get('price')
            )
            if cost is not None:
                print(f"[METERING] ✅ Found cost in llm_output.usage: ${cost}")
                return Decimal(str(cost))
        
        # Check 5: Check kwargs for cost (sometimes passed through kwargs)
        # This is handled in on_llm_end via kwargs parameter
        
        print(f"[METERING] ⚠️ No cost found in response - will use pricing table estimate")
        return None
    
    def _calculate_cost(
        self,
        llm_output: dict,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Decimal:
        """Calculate cost from LLM response.
        
        First tries to get cost directly from the response (some providers include it).
        Falls back to estimating based on model pricing.
        """
        # Some providers include cost directly in the response
        if "cost" in llm_output:
            return Decimal(str(llm_output["cost"]))
        
        # OpenAI sometimes includes it in usage
        usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
        if "total_cost" in usage:
            return Decimal(str(usage["total_cost"]))
        
        # Check response_metadata for cost (OpenAI sometimes includes it there)
        # This is checked in on_llm_end before calling _calculate_cost
        # But we can also check here as a fallback
        
        # Estimate based on model pricing
        return self._estimate_cost(model, input_tokens, output_tokens)
    
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Estimate cost based on model pricing tables.
        
        Uses official pricing from provider documentation.
        OpenAI API does NOT return cost - we calculate it from tokens × pricing.
        Pricing can be overridden via {KLUISZ_CONFIG_DIR}/pricing_config.json
        """
        model_lower = model.lower()
        pricing = self.get_model_pricing()
        
        # Find matching model pricing (more specific models checked first)
        for model_key, (input_price, output_price) in pricing.items():
            if model_key in model_lower:
                input_cost = input_tokens / 1000 * input_price
                output_cost = output_tokens / 1000 * output_price
                cost = input_cost + output_cost
                print(f"[METERING] 💰 Pricing matched '{model_key}': "
                      f"input={input_tokens}×${input_price}/1K=${input_cost:.6f}, "
                      f"output={output_tokens}×${output_price}/1K=${output_cost:.6f}, "
                      f"total=${cost:.6f}")
                return Decimal(str(round(cost, 8)))
        
        # Default fallback pricing
        input_price, output_price = pricing.get("default", (0.002, 0.006))
        input_cost = input_tokens / 1000 * input_price
        output_cost = output_tokens / 1000 * output_price
        cost = input_cost + output_cost
        print(f"[METERING] ⚠️ No pricing match for '{model}', using default: "
              f"input={input_tokens}×${input_price}/1K=${input_cost:.6f}, "
              f"output={output_tokens}×${output_price}/1K=${output_cost:.6f}, "
              f"total=${cost:.6f}")
        return Decimal(str(round(cost, 8)))
    
    def get_accumulated_usage(self) -> dict[str, Any]:
        """Get accumulated usage statistics for this trace."""
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "flow_id": self.flow_id,
            "trace_id": self.trace_id,
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
            "total_tokens": self._total_tokens,
            "total_cost_usd": float(self._total_cost),
            "llm_calls_count": len(self._llm_calls),
            "llm_calls": self._llm_calls,
        }
    
    async def finalize_and_deduct(self) -> dict[str, Any]:
        """Finalize metering and deduct credits from user.
        
        Called at the end of the trace to:
        1. Get user's license tier
        2. Calculate credits based on cost and tier's credits_per_usd
        3. Deduct credits from user
        4. Create transaction record
        
        Returns:
            Dictionary with deduction details or error
        """
        print(f"\n{'='*60}")
        print(
            f"[METERING] finalize_and_deduct called: "
            f"user={self.user_id[:8] if self.user_id else 'None'}..., "
            f"total_tokens={self._total_tokens}, "
            f"total_cost=${self._total_cost}, "
            f"llm_calls={len(self._llm_calls)}"
        )
        
        # Skip if no cost incurred
        if self._total_cost <= 0:
            return {
                "credits_deducted": 0,
                "cost_usd": 0,
                "reason": "no_cost_incurred",
            }
        
        try:
            from datetime import datetime, timezone
            
            from klx.services.deps import session_scope
            from kluisz.schema.serialize import str_to_uuid
            from kluisz.services.database.models.user.model import User
            from kluisz.services.database.models.transactions.model import TransactionTable
            from kluisz.services.database.models.license_tier.model import LicenseTier
            
            async with session_scope() as session:
                # Get user
                user = await session.get(User, str_to_uuid(self.user_id))
                if not user:
                    logger.warning(f"User {self.user_id} not found for credit deduction")
                    return {"error": "User not found", "credits_deducted": 0}
                
                # Skip if platform superadmin (no billing)
                if user.is_platform_superadmin:
                    print(f"[METERING] 👑 Superadmin detected - no billing")
                    print(f"[METERING]    └─ Tokens: {self._total_tokens:,}, Cost: ${self._total_cost:.6f} (not charged)")
                    return {
                        "credits_deducted": 0,
                        "reason": "superadmin",
                        "cost_usd": float(self._total_cost),
                        "tokens": self._total_tokens,
                    }
                
                # Skip if no active license
                if not user.license_is_active or not user.license_tier_id:
                    print(f"[METERING] ⚠️ No active license - skipping deduction")
                    print(f"[METERING]    └─ license_is_active={user.license_is_active}, tier_id={user.license_tier_id}")
                    return {
                        "credits_deducted": 0,
                        "reason": "no_active_license",
                        "cost_usd": float(self._total_cost),
                        "tokens": self._total_tokens,
                    }
                
                # Get license tier for credits_per_usd
                tier = await session.get(LicenseTier, user.license_tier_id)
                if not tier:
                    logger.warning(f"User {self.user_id} not found for credit deduction")
                    print(f"[METERING] ❌ License tier {user.license_tier_id} not found!")
                    return {"error": "License tier not found", "credits_deducted": 0}
                
                print(f"[METERING] 📋 User License Info:")
                print(f"[METERING]    └─ Tier: {tier.name} (id: {str(tier.id)[:8]}...)")
                print(f"[METERING]    └─ Credits per USD: {tier.credits_per_usd}")
                print(f"[METERING]    └─ Pricing multiplier: {tier.pricing_multiplier or 1.0}")
                
                # Calculate credits from cost
                credits_per_usd = Decimal(str(tier.credits_per_usd or 100))
                
                # Apply pricing multiplier if set
                adjusted_cost = self._total_cost
                if tier.pricing_multiplier:
                    adjusted_cost = self._total_cost * Decimal(str(tier.pricing_multiplier))
                    print(f"[METERING] 💵 Cost Adjustment:")
                    print(f"[METERING]    └─ Original cost: ${self._total_cost}")
                    print(f"[METERING]    └─ Multiplier: {tier.pricing_multiplier}")
                    print(f"[METERING]    └─ Adjusted cost: ${adjusted_cost}")
                
                credits = int(adjusted_cost * credits_per_usd)
                
                print(f"[METERING] 🧮 Credit Calculation:")
                print(f"[METERING]    └─ Cost USD: ${adjusted_cost}")
                print(f"[METERING]    └─ Credits per USD: {credits_per_usd}")
                print(f"[METERING]    └─ Formula: ${adjusted_cost} × {credits_per_usd} = {credits} credits")
                
                # Ensure at least 1 credit for any LLM usage
                if credits == 0 and self._total_tokens > 0:
                    credits = 1
                    print(f"[METERING]    └─ Minimum credit applied: 1 credit (tokens > 0)")
                
                if credits <= 0:
                    print(f"[METERING] ⚠️ Zero credits calculated, skipping deduction")
                    return {
                        "credits_deducted": 0,
                        "cost_usd": float(self._total_cost),
                        "tokens": self._total_tokens,
                        "reason": "zero_credits_calculated",
                    }
                
                # Calculate balances
                credits_before = (user.credits_allocated or 0) - (user.credits_used or 0)
                
                # Deduct credits
                user.credits_used = (user.credits_used or 0) + credits
                user.updated_at = datetime.now(timezone.utc)
                
                credits_after = (user.credits_allocated or 0) - (user.credits_used or 0)
                
                print(f"[METERING] 💳 Credit Deduction:")
                print(f"[METERING]    └─ Credits before: {credits_before}")
                print(f"[METERING]    └─ Credits deducted: {credits}")
                print(f"[METERING]    └─ Credits after: {credits_after}")
                
                # Create transaction record
                # Aggregate model usage for efficient storage
                model_usage_summary: dict[str, dict[str, Any]] = {}
                for call in self._llm_calls:
                    model = call.get("model", "unknown")
                    if model not in model_usage_summary:
                        model_usage_summary[model] = {
                            "total_tokens": 0,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "total_cost_usd": 0.0,
                            "call_count": 0,
                        }
                    model_usage_summary[model]["total_tokens"] += call.get("total_tokens", 0)
                    model_usage_summary[model]["input_tokens"] += call.get("input_tokens", 0)
                    model_usage_summary[model]["output_tokens"] += call.get("output_tokens", 0)
                    model_usage_summary[model]["total_cost_usd"] += call.get("cost_usd", 0.0)
                    model_usage_summary[model]["call_count"] += 1
                
                # Log model usage breakdown
                if model_usage_summary:
                    print(f"[METERING] 📊 Model Usage Breakdown:")
                    for model_name, usage in model_usage_summary.items():
                        print(f"[METERING]    └─ {model_name}:")
                        print(f"[METERING]       ├─ Calls: {usage['call_count']}")
                        print(f"[METERING]       ├─ Tokens: {usage['total_tokens']:,} (in:{usage['input_tokens']:,}, out:{usage['output_tokens']:,})")
                        print(f"[METERING]       └─ Cost: ${usage['total_cost_usd']:.6f}")
                
                transaction = TransactionTable(
                    id=uuid4(),
                    user_id=str_to_uuid(self.user_id),
                    flow_id=str_to_uuid(self.flow_id) if self.flow_id else None,
                    transaction_type="deduction",
                    credits_amount=credits,
                    credits_before=credits_before,
                    credits_after=credits_after,
                    usage_record_id=self.trace_id,
                    transaction_metadata={
                        "source": "metering_callback",
                        "input_tokens": self._total_input_tokens,
                        "output_tokens": self._total_output_tokens,
                        "total_tokens": self._total_tokens,
                        "cost_usd": float(self._total_cost),
                        "adjusted_cost_usd": float(adjusted_cost),
                        "tier_id": str(user.license_tier_id),
                        "tier_name": tier.name,
                        "credits_per_usd": float(credits_per_usd),
                        "llm_calls_count": len(self._llm_calls),
                        "model_usage": model_usage_summary,  # Store aggregated model usage
                    },
                    created_by=str_to_uuid(self.user_id),
                    # timestamp is auto-set by default_factory
                )
                
                session.add(user)
                session.add(transaction)
                await session.commit()
                
                # Final summary
                print(f"[METERING] ✅ BILLING COMPLETE:")
                print(f"[METERING]    ├─ Transaction ID: {str(transaction.id)[:8]}...")
                print(f"[METERING]    ├─ User: {self.user_id[:8]}...")
                print(f"[METERING]    ├─ Tier: {tier.name}")
                print(f"[METERING]    ├─ Tokens used: {self._total_tokens:,}")
                print(f"[METERING]    ├─ Cost USD: ${self._total_cost:.6f}")
                if tier.pricing_multiplier and tier.pricing_multiplier != 1.0:
                    print(f"[METERING]    ├─ Adjusted cost: ${adjusted_cost:.6f} (×{tier.pricing_multiplier})")
                print(f"[METERING]    ├─ Credits deducted: {credits}")
                print(f"[METERING]    └─ Balance: {credits_before} → {credits_after}")
                print(f"{'='*60}\n")
                
                result = {
                    "credits_deducted": credits,
                    "cost_usd": float(self._total_cost),
                    "adjusted_cost_usd": float(adjusted_cost),
                    "tokens": self._total_tokens,
                    "credits_before": credits_before,
                    "credits_after": credits_after,
                    "transaction_id": str(transaction.id),
                    "tier_name": tier.name,
                }
                print(f"[METERING] Result: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error deducting credits in metering callback: {e}")
            print(f"[METERING] ❌ ERROR: {e}")
            return {"error": str(e), "credits_deducted": 0}

