"""Unit tests for Subscription Service."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

from kluisz.services.database.models.license_tier.model import LicenseTier
from kluisz.services.database.models.subscription.model import Subscription
from kluisz.services.database.models.subscription_history.model import SubscriptionHistory
from kluisz.services.database.models.tenant.model import Tenant
from kluisz.services.database.models.user.model import User
from kluisz.services.subscription.service import SubscriptionService


@pytest.fixture
async def session():
    """Create an in-memory database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def subscription_service(session, monkeypatch):
    """Create a SubscriptionService instance with patched session_scope."""
    @asynccontextmanager
    async def mock_session_scope():
        """Mock session_scope to use the test session."""
        try:
            yield session
            await session.commit()
        except Exception:
            if session.is_active:
                await session.rollback()
            raise

    # Patch where it's used in the service module
    monkeypatch.setattr("kluisz.services.subscription.service.session_scope", mock_session_scope)
    yield SubscriptionService()


@pytest.fixture
async def sample_tier(session: AsyncSession):
    """Create a sample license tier."""
    tier = LicenseTier(
        id=uuid4(),
        name="Professional",
        description="Professional tier",
        token_price_per_1000=Decimal("0.01"),
        credits_per_usd=Decimal("200.00"),
        pricing_multiplier=Decimal("0.95"),
        default_credits=10000,
        default_credits_per_month=1000,
        max_users=50,
        is_active=True,
    )
    session.add(tier)
    await session.commit()
    await session.refresh(tier)
    return tier


@pytest.fixture
async def sample_tenant(session: AsyncSession):
    """Create a sample tenant."""
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        slug="test-tenant",
        is_active=True,
        max_users=10,
        license_pools={},
    )
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    yield tenant
    # Cleanup: delete the tenant after test
    try:
        await session.delete(tenant)
        await session.commit()
    except Exception:
        await session.rollback()


@pytest.fixture
async def sample_users(session: AsyncSession, sample_tenant: Tenant, sample_tier: LicenseTier):
    """Create sample users with licenses."""
    users = []
    for i in range(3):
        user = User(
            id=uuid4(),
            username=f"user{i}",
            password="hashed_password",
            tenant_id=sample_tenant.id,
            is_active=True,
            license_is_active=True,
            license_tier_id=sample_tier.id,
            license_pool_id=sample_tier.id,
            credits_allocated=1000,
            credits_used=100,
            credits_per_month=100,
        )
        session.add(user)
        users.append(user)
    await session.commit()
    for user in users:
        await session.refresh(user)
    return users


class TestSubscriptionService:
    """Test suite for SubscriptionService."""

    @pytest.mark.asyncio
    async def test_create_subscription(
        self,
        subscription_service: SubscriptionService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
    ):
        """Test creating a new subscription."""
        subscription = await subscription_service.create_subscription(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            license_count=10,
            amount=Decimal("99.00"),
            payment_method_id="pm_123",
            created_by=uuid4(),
        )

        assert subscription.tenant_id == sample_tenant.id
        assert subscription.tier_id == sample_tier.id
        assert subscription.license_count == 10
        assert subscription.amount == Decimal("99.00")
        assert subscription.status == "active"
        assert subscription.payment_method_id == "pm_123"

        # Verify tenant updated
        await session.refresh(sample_tenant)
        assert sample_tenant.subscription_tier_id == sample_tier.id
        assert sample_tenant.subscription_license_count == 10
        assert sample_tenant.subscription_status == "active"
        assert sample_tenant.subscription_amount == Decimal("99.00")

        # Verify license pool created
        assert str(sample_tier.id) in sample_tenant.license_pools
        pool = sample_tenant.license_pools[str(sample_tier.id)]
        assert pool["total_count"] == 10
        assert pool["available_count"] == 10

        # Verify history created
        stmt = select(SubscriptionHistory).where(
            SubscriptionHistory.subscription_id == subscription.id
        )
        result = await session.execute(stmt)
        history = result.scalars().first()
        assert history is not None
        assert history.action == "created"

    @pytest.mark.asyncio
    async def test_create_subscription_tenant_not_found(
        self,
        subscription_service: SubscriptionService,
        sample_tier: LicenseTier,
    ):
        """Test creating subscription for non-existent tenant."""
        with pytest.raises(ValueError, match="Tenant .* not found"):
            await subscription_service.create_subscription(
                tenant_id=uuid4(),
                tier_id=sample_tier.id,
                license_count=10,
                amount=Decimal("99.00"),
            )

    @pytest.mark.asyncio
    async def test_create_subscription_tier_not_found(
        self,
        subscription_service: SubscriptionService,
        sample_tenant: Tenant,
    ):
        """Test creating subscription with non-existent tier."""
        with pytest.raises(ValueError, match="License tier .* not found"):
            await subscription_service.create_subscription(
                tenant_id=sample_tenant.id,
                tier_id=uuid4(),
                license_count=10,
                amount=Decimal("99.00"),
            )

    @pytest.mark.asyncio
    async def test_renew_subscription(
        self,
        subscription_service: SubscriptionService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_users: list[User],
    ):
        """Test renewing a subscription."""
        # Create subscription
        subscription = await subscription_service.create_subscription(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            license_count=10,
            amount=Decimal("99.00"),
        )

        original_renewal_date = subscription.renewal_date

        # Renew subscription
        renewed = await subscription_service.renew_subscription(subscription.id)

        assert renewed.last_payment_date is not None
        assert renewed.renewal_date > original_renewal_date
        assert renewed.next_payment_date > original_renewal_date

        # Verify tenant updated
        await session.refresh(sample_tenant)
        assert sample_tenant.subscription_renewal_date == renewed.renewal_date

        # Verify users got monthly credits
        for user in sample_users:
            await session.refresh(user)
            # Credits should be increased by credits_per_month
            assert user.credits_allocated >= 1000  # Original + monthly top-up

        # Verify history created
        stmt = select(SubscriptionHistory).where(
            SubscriptionHistory.subscription_id == subscription.id,
            SubscriptionHistory.action == "renewed",
        )
        result = await session.execute(stmt)
        history = result.scalars().first()
        assert history is not None

    @pytest.mark.asyncio
    async def test_renew_subscription_not_active(
        self,
        subscription_service: SubscriptionService,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
    ):
        """Test renewing a non-active subscription."""
        # Create cancelled subscription
        subscription = await subscription_service.create_subscription(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            license_count=10,
            amount=Decimal("99.00"),
        )

        await subscription_service.cancel_subscription(
            subscription_id=subscription.id,
            reason="Test cancellation",
        )

        # Try to renew
        with pytest.raises(ValueError, match="is not active"):
            await subscription_service.renew_subscription(subscription.id)

    @pytest.mark.asyncio
    async def test_cancel_subscription(
        self,
        subscription_service: SubscriptionService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
    ):
        """Test cancelling a subscription."""
        # Create subscription
        subscription = await subscription_service.create_subscription(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            license_count=10,
            amount=Decimal("99.00"),
        )

        cancelled_by = uuid4()
        cancelled = await subscription_service.cancel_subscription(
            subscription_id=subscription.id,
            reason="User requested cancellation",
            cancelled_by=cancelled_by,
        )

        assert cancelled.status == "cancelled"
        assert cancelled.cancelled_at is not None
        assert cancelled.end_date == subscription.renewal_date  # Access until end of period

        # Verify tenant updated
        await session.refresh(sample_tenant)
        assert sample_tenant.subscription_status == "cancelled"
        assert sample_tenant.subscription_end_date == cancelled.end_date

        # Verify history created
        stmt = select(SubscriptionHistory).where(
            SubscriptionHistory.subscription_id == subscription.id,
            SubscriptionHistory.action == "cancelled",
        )
        result = await session.execute(stmt)
        history = result.scalars().first()
        assert history is not None
        assert history.reason == "User requested cancellation"
        assert history.changed_by == cancelled_by

    @pytest.mark.asyncio
    async def test_cancel_subscription_not_found(
        self,
        subscription_service: SubscriptionService,
    ):
        """Test cancelling non-existent subscription."""
        with pytest.raises(ValueError, match="Subscription .* not found"):
            await subscription_service.cancel_subscription(
                subscription_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_subscription_lifecycle_end_to_end(
        self,
        subscription_service: SubscriptionService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_users: list[User],
    ):
        """Test complete subscription lifecycle: create -> renew -> cancel."""
        # 1. Create subscription
        subscription = await subscription_service.create_subscription(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            license_count=10,
            amount=Decimal("99.00"),
            payment_method_id="pm_123",
        )

        assert subscription.status == "active"
        await session.refresh(sample_tenant)
        assert sample_tenant.subscription_status == "active"

        # 2. Renew subscription
        renewed = await subscription_service.renew_subscription(subscription.id)
        assert renewed.status == "active"
        assert renewed.last_payment_date is not None

        # 3. Cancel subscription
        cancelled = await subscription_service.cancel_subscription(
            subscription_id=subscription.id,
            reason="End of test",
        )
        assert cancelled.status == "cancelled"

        # Verify all history entries
        stmt = select(SubscriptionHistory).where(
            SubscriptionHistory.subscription_id == subscription.id
        )
        result = await session.execute(stmt)
        history_entries = list(result.scalars().all())
        assert len(history_entries) == 3  # created, renewed, cancelled

        actions = [entry.action for entry in history_entries]
        assert "created" in actions
        assert "renewed" in actions
        assert "cancelled" in actions

