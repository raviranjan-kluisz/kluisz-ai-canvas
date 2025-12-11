"""End-to-end integration tests for licensing and subscription system."""

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
from kluisz.services.database.models.transactions.model import TransactionTable
from kluisz.services.database.models.user.model import User
from kluisz.services.license.service import LicenseService
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
async def license_service(session, monkeypatch):
    """Create a LicenseService instance with patched session_scope."""
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
    monkeypatch.setattr("kluisz.services.license.service.session_scope", mock_session_scope)
    yield LicenseService()


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
async def setup_data(session: AsyncSession):
    """Set up test data: tiers, tenant, users."""
    # Create tiers
    starter_tier = LicenseTier(
        id=uuid4(),
        name="Starter",
        default_credits=1000,
        default_credits_per_month=100,
        credits_per_usd=Decimal("100.00"),
        pricing_multiplier=Decimal("1.00"),
        is_active=True,
    )
    pro_tier = LicenseTier(
        id=uuid4(),
        name="Professional",
        default_credits=10000,
        default_credits_per_month=1000,
        credits_per_usd=Decimal("200.00"),
        pricing_multiplier=Decimal("0.95"),
        is_active=True,
    )
    session.add(starter_tier)
    session.add(pro_tier)
    await session.commit()

    # Create test tenant
    tenant = Tenant(
        id=uuid4(),
        name="Test Company",
        slug="test-company",
        is_active=True,
        max_users=10,
        license_pools={},
    )
    session.add(tenant)
    await session.commit()

    # Create users
    admin_user = User(
        id=uuid4(),
        username="admin",
        password="hashed",
        tenant_id=tenant.id,
        is_active=True,
        is_tenant_admin=True,
        license_is_active=False,
    )
    user1 = User(
        id=uuid4(),
        username="user1",
        password="hashed",
        tenant_id=tenant.id,
        is_active=True,
        license_is_active=False,
    )
    user2 = User(
        id=uuid4(),
        username="user2",
        password="hashed",
        tenant_id=tenant.id,
        is_active=True,
        license_is_active=False,
    )
    session.add(admin_user)
    session.add(user1)
    session.add(user2)
    await session.commit()

    yield {
        "starter_tier": starter_tier,
        "pro_tier": pro_tier,
        "tenant": tenant,
        "admin_user": admin_user,
        "user1": user1,
        "user2": user2,
    }
    
    # Cleanup: delete test tenant and related data after test
    try:
        # Delete users first (foreign key constraint)
        await session.delete(user1)
        await session.delete(user2)
        await session.delete(admin_user)
        # Delete tenant
        await session.delete(tenant)
        # Delete tiers
        await session.delete(starter_tier)
        await session.delete(pro_tier)
        await session.commit()
    except Exception:
        await session.rollback()


class TestLicensingE2E:
    """End-to-end tests for complete licensing workflow."""

    @pytest.mark.asyncio
    async def test_complete_license_lifecycle(
        self,
        session: AsyncSession,
        license_service: LicenseService,
        subscription_service: SubscriptionService,
        setup_data: dict,
    ):
        """Test complete license lifecycle: subscription -> pools -> assignments -> usage."""
        starter_tier = setup_data["starter_tier"]
        pro_tier = setup_data["pro_tier"]
        tenant = setup_data["tenant"]
        admin_user = setup_data["admin_user"]
        user1 = setup_data["user1"]
        user2 = setup_data["user2"]

        # 1. Create subscription for Professional tier
        subscription = await subscription_service.create_subscription(
            tenant_id=tenant.id,
            tier_id=pro_tier.id,
            license_count=5,
            amount=Decimal("199.00"),
            payment_method_id="pm_123",
            created_by=admin_user.id,
        )

        assert subscription.status == "active"
        await session.refresh(tenant)
        assert tenant.subscription_status == "active"
        assert str(pro_tier.id) in tenant.license_pools

        # 2. Create additional pool for Starter tier (manual assignment)
        pool = await license_service.create_or_update_pool_for_tier(
            tenant_id=tenant.id,
            tier_id=starter_tier.id,
            total_count=3,
            created_by=admin_user.id,
        )

        assert pool["total_count"] == 3
        assert pool["available_count"] == 3

        # 3. Assign Professional license to user1
        assigned_user1 = await license_service.assign_license_to_user(
            user_id=user1.id,
            tier_id=pro_tier.id,
            assigned_by=admin_user.id,
        )

        assert assigned_user1.license_is_active is True
        assert assigned_user1.license_tier_id == pro_tier.id
        assert assigned_user1.credits_allocated == pro_tier.default_credits

        # 4. Assign Starter license to user2
        assigned_user2 = await license_service.assign_license_to_user(
            user_id=user2.id,
            tier_id=starter_tier.id,
            assigned_by=admin_user.id,
        )

        assert assigned_user2.license_is_active is True
        assert assigned_user2.license_tier_id == starter_tier.id

        # 5. Verify pool counts
        await session.refresh(tenant)
        pro_pool = tenant.license_pools[str(pro_tier.id)]
        starter_pool = tenant.license_pools[str(starter_tier.id)]

        assert pro_pool["assigned_count"] == 1
        assert pro_pool["available_count"] == 4
        assert starter_pool["assigned_count"] == 1
        assert starter_pool["available_count"] == 2

        # 6. User1 uses credits
        user1_after_deduction = await license_service.deduct_credits(
            user_id=user1.id,
            credits=500,
            usage_record_id="trace_001",
            metadata={"model": "gpt-4", "tokens": 10000},
        )

        assert user1_after_deduction.credits_used == 500
        assert (
            user1_after_deduction.credits_allocated - user1_after_deduction.credits_used
            == pro_tier.default_credits - 500
        )

        # 7. Verify transaction created
        stmt = select(TransactionTable).where(
            TransactionTable.user_id == user1.id,
            TransactionTable.transaction_type == "deduction",
        )
        result = await session.execute(stmt)
        transaction = result.scalars().first()
        assert transaction is not None
        assert transaction.credits_amount == 500
        assert transaction.usage_record_id == "trace_001"

        # 8. Upgrade user2 from Starter to Professional
        upgraded_user2 = await license_service.upgrade_user_license(
            user_id=user2.id,
            new_tier_id=pro_tier.id,
            assigned_by=admin_user.id,
            preserve_credits=False,
        )

        assert upgraded_user2.license_tier_id == pro_tier.id
        assert upgraded_user2.credits_allocated == pro_tier.default_credits

        # 9. Verify pool counts after upgrade
        await session.refresh(tenant)
        pro_pool_after = tenant.license_pools[str(pro_tier.id)]
        starter_pool_after = tenant.license_pools[str(starter_tier.id)]

        assert pro_pool_after["assigned_count"] == 2
        assert pro_pool_after["available_count"] == 3
        assert starter_pool_after["assigned_count"] == 0
        assert starter_pool_after["available_count"] == 3

        # 10. Renew subscription (monthly credits top-up)
        original_renewal_date = subscription.renewal_date
        renewed = await subscription_service.renew_subscription(subscription.id)

        assert renewed.last_payment_date is not None
        assert renewed.renewal_date > original_renewal_date

        # Verify users got monthly credits
        await session.refresh(user1)
        await session.refresh(upgraded_user2)
        # Credits should be increased by credits_per_month
        assert user1.credits_allocated >= pro_tier.default_credits
        assert upgraded_user2.credits_allocated >= pro_tier.default_credits

        # 11. Unassign license from user1
        unassigned_user1 = await license_service.unassign_license_from_user(user1.id)

        assert unassigned_user1.license_is_active is False
        assert unassigned_user1.license_tier_id is None

        # 12. Verify final pool counts
        await session.refresh(tenant)
        final_pro_pool = tenant.license_pools[str(pro_tier.id)]
        assert final_pro_pool["assigned_count"] == 1
        assert final_pro_pool["available_count"] == 4

    @pytest.mark.asyncio
    async def test_subscription_with_multiple_renewals(
        self,
        session: AsyncSession,
        subscription_service: SubscriptionService,
        license_service: LicenseService,
        setup_data: dict,
    ):
        """Test subscription with multiple renewals and credit top-ups."""
        pro_tier = setup_data["pro_tier"]
        tenant = setup_data["tenant"]
        admin_user = setup_data["admin_user"]
        user1 = setup_data["user1"]

        # Create subscription
        subscription = await subscription_service.create_subscription(
            tenant_id=tenant.id,
            tier_id=pro_tier.id,
            license_count=10,
            amount=Decimal("199.00"),
            created_by=admin_user.id,
        )

        # Assign license
        await license_service.assign_license_to_user(
            user_id=user1.id,
            tier_id=pro_tier.id,
            assigned_by=admin_user.id,
        )

        initial_credits = user1.credits_allocated

        # First renewal
        await subscription_service.renew_subscription(subscription.id)
        await session.refresh(user1)
        credits_after_first = user1.credits_allocated
        assert credits_after_first > initial_credits

        # Second renewal
        await subscription_service.renew_subscription(subscription.id)
        await session.refresh(user1)
        credits_after_second = user1.credits_allocated
        assert credits_after_second > credits_after_first

        # Verify history entries
        stmt = select(SubscriptionHistory).where(
            SubscriptionHistory.subscription_id == subscription.id
        )
        result = await session.execute(stmt)
        history_entries = list(result.scalars().all())
        assert len(history_entries) >= 2  # created + renewals

    @pytest.mark.asyncio
    async def test_concurrent_license_assignments(
        self,
        session: AsyncSession,
        license_service: LicenseService,
        setup_data: dict,
    ):
        """Test concurrent license assignments (edge case handling)."""
        pro_tier = setup_data["pro_tier"]
        tenant = setup_data["tenant"]
        admin_user = setup_data["admin_user"]
        user1 = setup_data["user1"]
        user2 = setup_data["user2"]

        # Create pool with only 1 license
        await license_service.create_or_update_pool_for_tier(
            tenant_id=tenant.id,
            tier_id=pro_tier.id,
            total_count=1,
            created_by=admin_user.id,
        )

        # Assign to user1 (should succeed)
        await license_service.assign_license_to_user(
            user_id=user1.id,
            tier_id=pro_tier.id,
            assigned_by=admin_user.id,
        )

        # Try to assign to user2 (should fail - no available)
        with pytest.raises(ValueError, match="No available licenses"):
            await license_service.assign_license_to_user(
                user_id=user2.id,
                tier_id=pro_tier.id,
                assigned_by=admin_user.id,
            )

        # Unassign from user1
        await license_service.unassign_license_from_user(user1.id)

        # Now user2 should be able to get it
        await license_service.assign_license_to_user(
            user_id=user2.id,
            tier_id=pro_tier.id,
            assigned_by=admin_user.id,
        )

        await session.refresh(user2)
        assert user2.license_is_active is True

    @pytest.mark.asyncio
    async def test_credit_transactions_tracking(
        self,
        session: AsyncSession,
        license_service: LicenseService,
        setup_data: dict,
    ):
        """Test that all credit operations create proper transaction records."""
        pro_tier = setup_data["pro_tier"]
        tenant = setup_data["tenant"]
        admin_user = setup_data["admin_user"]
        user1 = setup_data["user1"]

        # Create pool and assign
        await license_service.create_or_update_pool_for_tier(
            tenant_id=tenant.id,
            tier_id=pro_tier.id,
            total_count=10,
        )

        await license_service.assign_license_to_user(
            user_id=user1.id,
            tier_id=pro_tier.id,
            assigned_by=admin_user.id,
        )

        # Deduct credits multiple times
        await license_service.deduct_credits(user1.id, 100, "trace_1")
        await license_service.deduct_credits(user1.id, 200, "trace_2")
        await license_service.deduct_credits(user1.id, 150, "trace_3")

        # Add credits
        await license_service.add_credits(user1.id, 500, admin_user.id)

        # Verify all transactions
        stmt = select(TransactionTable).where(TransactionTable.user_id == user1.id)
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        assert len(transactions) == 4  # 3 deductions + 1 addition

        deduction_transactions = [
            t for t in transactions if t.transaction_type == "deduction"
        ]
        addition_transactions = [
            t for t in transactions if t.transaction_type == "addition"
        ]

        assert len(deduction_transactions) == 3
        assert len(addition_transactions) == 1

        # Verify credits balance
        total_deductions = sum(t.credits_amount for t in deduction_transactions)
        total_additions = sum(t.credits_amount for t in addition_transactions)

        await session.refresh(user1)
        expected_balance = (
            pro_tier.default_credits - total_deductions + total_additions
        )
        actual_balance = user1.credits_allocated - user1.credits_used

        assert actual_balance == expected_balance

