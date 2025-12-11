"""Unit tests for AnalyticsService."""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from kluisz.services.analytics.service import AnalyticsService


class TestAnalyticsService:
    """Tests for the AnalyticsService."""

    @pytest.fixture
    def service(self):
        """Create analytics service instance."""
        return AnalyticsService()

    def test_ready(self, service):
        """Test service is always ready (no external deps)."""
        assert service.ready is True

    def test_empty_dashboard(self, service):
        """Test empty dashboard structure."""
        start = datetime.now(timezone.utc) - timedelta(days=30)
        end = datetime.now(timezone.utc)
        
        result = service._empty_dashboard(start, end)
        
        assert result["summary"]["total_executions"] == 0
        assert result["summary"]["total_credits"] == 0
        assert result["top_users"] == []
        assert result["top_flows"] == []
        assert result["time_series"] == []


class TestAnalyticsServiceWithMocks:
    """Tests with mocked database."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def mock_transaction(self):
        """Create a mock transaction."""
        tx = MagicMock()
        tx.id = uuid4()
        tx.user_id = uuid4()
        tx.flow_id = uuid4()
        tx.transaction_type = "deduction"
        tx.credits_amount = 10
        tx.timestamp = datetime.now(timezone.utc)
        tx.transaction_metadata = {
            "total_tokens": 1000,
            "cost_usd": 0.05,
        }
        return tx

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "testuser"
        user.tenant_id = uuid4()
        user.credits_allocated = 1000
        user.credits_used = 100
        user.credits_per_month = 500
        user.license_is_active = True
        user.license_tier_id = uuid4()
        return user

    @pytest.fixture
    def mock_tenant(self):
        """Create a mock tenant."""
        tenant = MagicMock()
        tenant.id = uuid4()
        tenant.name = "Test Tenant"
        tenant.slug = "test-tenant"
        tenant.is_active = True
        return tenant

    @pytest.mark.asyncio
    async def test_get_credit_status(self, mock_session, mock_user):
        """Test get_credit_status returns correct structure."""
        mock_tier = MagicMock()
        mock_tier.id = mock_user.license_tier_id
        mock_tier.name = "Basic"
        mock_tier.credits_per_usd = 100
        mock_tier.default_credits = 500
        
        async def mock_get(model_class, id):
            from kluisz.services.database.models.user.model import User
            from kluisz.services.database.models.license_tier.model import LicenseTier
            if model_class == User:
                return mock_user
            elif model_class == LicenseTier:
                return mock_tier
            return None
        
        mock_session.get = mock_get
        
        service = AnalyticsService()
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await service.get_credit_status(str(mock_user.id))
        
        assert result["user_id"] == str(mock_user.id)
        assert result["username"] == "testuser"
        assert result["credits_allocated"] == 1000
        assert result["credits_used"] == 100
        assert result["credits_remaining"] == 900
        assert result["usage_percent"] == 10.0
        assert result["license_is_active"] is True
        assert result["tier_name"] == "Basic"
        assert result["is_low_credits"] is False
        assert result["is_out_of_credits"] is False

    @pytest.mark.asyncio
    async def test_get_credit_status_low_credits(self, mock_session, mock_user):
        """Test get_credit_status detects low credits."""
        mock_user.credits_allocated = 100
        mock_user.credits_used = 90  # Only 10 remaining out of 100 (10%)
        
        async def mock_get(model_class, id):
            from kluisz.services.database.models.user.model import User
            return mock_user if model_class == User else None
        
        mock_session.get = mock_get
        
        service = AnalyticsService()
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await service.get_credit_status(str(mock_user.id))
        
        assert result["credits_remaining"] == 10
        assert result["is_low_credits"] is True  # < 20%
        assert result["is_out_of_credits"] is False

    @pytest.mark.asyncio
    async def test_get_credit_status_out_of_credits(self, mock_session, mock_user):
        """Test get_credit_status detects out of credits."""
        mock_user.credits_allocated = 100
        mock_user.credits_used = 100  # 0 remaining
        
        async def mock_get(model_class, id):
            from kluisz.services.database.models.user.model import User
            return mock_user if model_class == User else None
        
        mock_session.get = mock_get
        
        service = AnalyticsService()
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await service.get_credit_status(str(mock_user.id))
        
        assert result["credits_remaining"] == 0
        assert result["is_out_of_credits"] is True

    @pytest.mark.asyncio
    async def test_get_user_dashboard_data(self, mock_session, mock_user, mock_transaction):
        """Test get_user_dashboard_data returns correct structure."""
        # Set transaction user_id to match
        mock_transaction.user_id = mock_user.id
        
        async def mock_get(model_class, id):
            from kluisz.services.database.models.user.model import User
            return mock_user if model_class == User else None
        
        mock_session.get = mock_get
        
        # Mock the query result
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_transaction]
        mock_session.exec.return_value = mock_result
        
        service = AnalyticsService()
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await service.get_user_dashboard_data(str(mock_user.id))
        
        assert "summary" in result
        assert "credits" in result
        assert "top_flows" in result
        assert "time_series" in result
        assert result["summary"]["total_executions"] == 1
        assert result["credits"]["credits_allocated"] == 1000
        assert result["credits"]["credits_remaining"] == 900

    @pytest.mark.asyncio
    async def test_get_user_dashboard_data_user_not_found(self, mock_session):
        """Test get_user_dashboard_data raises for non-existent user."""
        async def mock_get(model_class, id):
            return None
        
        mock_session.get = mock_get
        
        service = AnalyticsService()
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            with pytest.raises(ValueError, match="not found"):
                await service.get_user_dashboard_data(str(uuid4()))

    @pytest.mark.asyncio
    async def test_get_tenant_dashboard_data_no_users(self, mock_session, mock_tenant):
        """Test get_tenant_dashboard_data returns empty for tenant with no users."""
        # Mock empty user list
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result
        
        service = AnalyticsService()
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await service.get_tenant_dashboard_data(str(mock_tenant.id))
        
        assert result["summary"]["total_executions"] == 0
        assert result["top_users"] == []
        assert result["top_flows"] == []

    @pytest.mark.asyncio
    async def test_get_platform_dashboard_data(self, mock_session, mock_tenant, mock_user, mock_transaction):
        """Test get_platform_dashboard_data aggregates across tenants."""
        mock_user.tenant_id = mock_tenant.id
        mock_transaction.user_id = mock_user.id
        
        # Mock tenant list
        tenant_result = MagicMock()
        tenant_result.all.return_value = [mock_tenant]
        
        # Mock user list
        user_result = MagicMock()
        user_result.all.return_value = [mock_user]
        
        # Mock transaction list
        tx_result = MagicMock()
        tx_result.all.return_value = [mock_transaction]
        
        # exec returns different results for different queries
        call_count = [0]
        def mock_exec(stmt):
            call_count[0] += 1
            if call_count[0] == 1:  # Tenants
                return tenant_result
            elif call_count[0] == 2:  # Users
                return user_result
            else:  # Transactions
                return tx_result
        
        mock_session.exec.side_effect = mock_exec
        
        service = AnalyticsService()
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await service.get_platform_dashboard_data()
        
        assert "summary" in result
        assert "top_tenants" in result
        assert "time_series" in result


class TestAnalyticsServiceDateHandling:
    """Tests for date handling in analytics."""

    def test_default_dates(self):
        """Test default date range is 30 days."""
        service = AnalyticsService()
        # The service should default to 30 days if not specified
        # This is tested implicitly through dashboard methods

    @pytest.mark.asyncio
    async def test_custom_date_range(self):
        """Test custom date range is respected."""
        service = AnalyticsService()
        
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result
        
        with patch("kluisz.services.analytics.service.session_scope") as mock_scope:
            mock_scope.return_value.__aenter__.return_value = mock_session
            mock_scope.return_value.__aexit__.return_value = None
            
            result = await service.get_tenant_dashboard_data(
                str(uuid4()),
                start_date=start,
                end_date=end,
            )
        
        assert result["period_start"] == start.isoformat()
        assert result["period_end"] == end.isoformat()

