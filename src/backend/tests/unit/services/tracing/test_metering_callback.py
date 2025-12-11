"""Unit tests for KluiszMeteringCallback."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from langchain_core.outputs import LLMResult


class TestKluiszMeteringCallback:
    """Tests for the metering callback."""

    @pytest.fixture
    def callback(self):
        """Create a metering callback instance."""
        from kluisz.services.tracing.metering_callback import KluiszMeteringCallback
        return KluiszMeteringCallback(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            flow_id=str(uuid4()),
            trace_id=str(uuid4()),
        )

    def test_init(self, callback):
        """Test callback initialization."""
        assert callback.user_id is not None
        assert callback.tenant_id is not None
        assert callback.flow_id is not None
        assert callback.trace_id is not None
        assert callback._total_tokens == 0
        assert callback._total_cost == Decimal("0.00")
        assert callback._llm_calls == []

    def test_estimate_cost_gpt4(self, callback):
        """Test cost estimation for GPT-4."""
        cost = callback._estimate_cost("gpt-4", 1000, 500)
        # GPT-4: $0.03/1K input, $0.06/1K output
        expected = Decimal(str((1000 / 1000 * 0.03) + (500 / 1000 * 0.06)))
        assert cost == expected

    def test_estimate_cost_gpt4o_mini(self, callback):
        """Test cost estimation for GPT-4o-mini."""
        cost = callback._estimate_cost("gpt-4o-mini", 1000, 500)
        # GPT-4o-mini: $0.00015/1K input, $0.0006/1K output
        expected = Decimal(str(round((1000 / 1000 * 0.00015) + (500 / 1000 * 0.0006), 8)))
        assert cost == expected

    def test_estimate_cost_claude(self, callback):
        """Test cost estimation for Claude."""
        cost = callback._estimate_cost("claude-3-sonnet", 1000, 500)
        # Claude 3 Sonnet: $0.003/1K input, $0.015/1K output
        expected = Decimal(str(round((1000 / 1000 * 0.003) + (500 / 1000 * 0.015), 8)))
        assert cost == expected

    def test_estimate_cost_unknown_model(self, callback):
        """Test cost estimation for unknown model uses default pricing."""
        cost = callback._estimate_cost("unknown-model", 1000, 500)
        # Default: $0.001/1K input, $0.002/1K output
        expected = Decimal(str(round((1000 / 1000 * 0.001) + (500 / 1000 * 0.002), 8)))
        assert cost == expected

    @pytest.mark.asyncio
    async def test_on_llm_end_captures_usage(self, callback):
        """Test that on_llm_end captures token usage."""
        # Create mock LLMResult
        response = LLMResult(
            generations=[],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                },
                "model_name": "gpt-4o-mini",
            }
        )
        
        await callback.on_llm_end(response)
        
        assert callback._total_input_tokens == 100
        assert callback._total_output_tokens == 50
        assert callback._total_tokens == 150
        assert callback._total_cost > 0
        assert len(callback._llm_calls) == 1
        assert callback._llm_calls[0]["model"] == "gpt-4o-mini"
        assert callback._llm_calls[0]["input_tokens"] == 100
        assert callback._llm_calls[0]["output_tokens"] == 50

    @pytest.mark.asyncio
    async def test_on_llm_end_accumulates_usage(self, callback):
        """Test that multiple on_llm_end calls accumulate usage."""
        response1 = LLMResult(
            generations=[],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                },
                "model_name": "gpt-4",
            }
        )
        response2 = LLMResult(
            generations=[],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 100,
                },
                "model_name": "gpt-4",
            }
        )
        
        await callback.on_llm_end(response1)
        await callback.on_llm_end(response2)
        
        assert callback._total_input_tokens == 300
        assert callback._total_output_tokens == 150
        assert callback._total_tokens == 450
        assert len(callback._llm_calls) == 2

    @pytest.mark.asyncio
    async def test_on_llm_end_handles_missing_usage(self, callback):
        """Test that on_llm_end handles missing usage data gracefully."""
        response = LLMResult(
            generations=[],
            llm_output={}
        )
        
        await callback.on_llm_end(response)
        
        assert callback._total_tokens == 0
        assert callback._total_cost == Decimal("0.00")

    def test_get_accumulated_usage(self, callback):
        """Test get_accumulated_usage returns correct structure."""
        callback._total_input_tokens = 100
        callback._total_output_tokens = 50
        callback._total_tokens = 150
        callback._total_cost = Decimal("0.05")
        callback._llm_calls = [{"model": "gpt-4", "tokens": 150}]
        
        usage = callback.get_accumulated_usage()
        
        assert usage["user_id"] == callback.user_id
        assert usage["tenant_id"] == callback.tenant_id
        assert usage["flow_id"] == callback.flow_id
        assert usage["trace_id"] == callback.trace_id
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["total_tokens"] == 150
        assert usage["total_cost_usd"] == 0.05
        assert usage["llm_calls_count"] == 1

    @pytest.mark.asyncio
    async def test_finalize_and_deduct_no_cost(self, callback):
        """Test finalize_and_deduct returns early if no cost."""
        result = await callback.finalize_and_deduct()
        
        assert result["credits_deducted"] == 0
        assert result["reason"] == "no_cost_incurred"

    @pytest.mark.asyncio
    async def test_finalize_and_deduct_with_cost(self, callback):
        """Test finalize_and_deduct deducts credits correctly."""
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.license_tier.model import LicenseTier
        
        # Set up cost
        callback._total_cost = Decimal("0.01")
        callback._total_tokens = 1000
        
        # Mock user and tier
        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()
        mock_user.is_platform_superadmin = False
        mock_user.license_is_active = True
        mock_user.license_tier_id = uuid4()
        mock_user.credits_allocated = 1000
        mock_user.credits_used = 0
        mock_user.updated_at = None
        
        mock_tier = MagicMock(spec=LicenseTier)
        mock_tier.id = mock_user.license_tier_id
        mock_tier.name = "Basic"
        mock_tier.credits_per_usd = 100  # 100 credits per $1
        mock_tier.pricing_multiplier = 1.0
        
        # Mock session
        async def mock_get(model_class, id):
            if model_class == User:
                return mock_user
            elif model_class == LicenseTier:
                return mock_tier
            return None
        
        mock_session = AsyncMock()
        mock_session.get = mock_get
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        
        with patch("kluisz.services.tracing.metering_callback.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await callback.finalize_and_deduct()
        
        # $0.01 * 100 credits/$ = 1 credit
        assert result["credits_deducted"] == 1
        assert result["cost_usd"] == 0.01
        assert "transaction_id" in result

    @pytest.mark.asyncio
    async def test_finalize_and_deduct_superadmin_bypass(self, callback):
        """Test that superadmins are not charged."""
        from kluisz.services.database.models.user.model import User
        
        callback._total_cost = Decimal("0.01")
        callback._total_tokens = 1000
        
        mock_user = MagicMock(spec=User)
        mock_user.is_platform_superadmin = True
        
        async def mock_get(model_class, id):
            return mock_user
        
        mock_session = AsyncMock()
        mock_session.get = mock_get
        
        with patch("kluisz.services.tracing.metering_callback.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await callback.finalize_and_deduct()
        
        assert result["credits_deducted"] == 0
        assert result["reason"] == "superadmin"

    @pytest.mark.asyncio
    async def test_finalize_and_deduct_no_license(self, callback):
        """Test that users without license are not charged."""
        from kluisz.services.database.models.user.model import User
        
        callback._total_cost = Decimal("0.01")
        callback._total_tokens = 1000
        
        mock_user = MagicMock(spec=User)
        mock_user.is_platform_superadmin = False
        mock_user.license_is_active = False
        mock_user.license_tier_id = None
        
        async def mock_get(model_class, id):
            return mock_user
        
        mock_session = AsyncMock()
        mock_session.get = mock_get
        
        with patch("kluisz.services.tracing.metering_callback.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await callback.finalize_and_deduct()
        
        assert result["credits_deducted"] == 0
        assert result["reason"] == "no_active_license"


class TestMeteringCallbackIntegration:
    """Integration tests for metering callback flow."""

    @pytest.mark.asyncio
    async def test_full_llm_flow(self):
        """Test a complete LLM call flow with metering."""
        from kluisz.services.tracing.metering_callback import KluiszMeteringCallback
        
        callback = KluiszMeteringCallback(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            flow_id=str(uuid4()),
            trace_id=str(uuid4()),
        )
        
        # Simulate multiple LLM calls in a flow
        responses = [
            LLMResult(
                generations=[],
                llm_output={
                    "token_usage": {"prompt_tokens": 500, "completion_tokens": 200},
                    "model_name": "gpt-4o",
                }
            ),
            LLMResult(
                generations=[],
                llm_output={
                    "token_usage": {"prompt_tokens": 300, "completion_tokens": 150},
                    "model_name": "gpt-4o",
                }
            ),
        ]
        
        for response in responses:
            await callback.on_llm_end(response)
        
        usage = callback.get_accumulated_usage()
        
        assert usage["total_tokens"] == 1150  # 500+200+300+150
        assert usage["llm_calls_count"] == 2
        assert usage["total_cost_usd"] > 0

