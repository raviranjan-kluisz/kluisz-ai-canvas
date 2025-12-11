"""Unit tests for License Service."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from kluisz.services.database.models.license_tier.model import LicenseTier
from kluisz.services.database.models.tenant.model import Tenant
from kluisz.services.database.models.transactions.model import TransactionTable
from kluisz.services.database.models.user.model import User
from kluisz.services.license.service import LicenseService


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
async def sample_user(session: AsyncSession, sample_tenant: Tenant):
    """Create a sample user."""
    user = User(
        id=uuid4(),
        username="testuser",
        password="hashed_password",
        tenant_id=sample_tenant.id,
        is_active=True,
        license_is_active=False,
        credits_allocated=0,
        credits_used=0,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


class TestLicenseService:
    """Test suite for LicenseService."""

    @pytest.mark.asyncio
    async def test_get_tenant_license_pools(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
    ):
        """Test getting tenant license pools."""
        # Set up pools
        sample_tenant.license_pools = {
            "tier_1": {
                "total_count": 10,
                "available_count": 5,
                "assigned_count": 5,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        }
        session.add(sample_tenant)
        await session.commit()

        pools = await license_service.get_tenant_license_pools(sample_tenant.id)
        assert "tier_1" in pools
        assert pools["tier_1"]["total_count"] == 10

    @pytest.mark.asyncio
    async def test_get_tenant_license_pools_not_found(
        self,
        license_service: LicenseService,
    ):
        """Test getting pools for non-existent tenant."""
        with pytest.raises(ValueError, match="Tenant .* not found"):
            await license_service.get_tenant_license_pools(uuid4())

    @pytest.mark.asyncio
    async def test_create_or_update_pool_for_tier(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
    ):
        """Test creating a new license pool."""
        pool = await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
            created_by=str(uuid4()),
        )

        assert pool["total_count"] == 10
        assert pool["available_count"] == 10
        assert pool["assigned_count"] == 0

        # Verify in database
        await session.refresh(sample_tenant)
        assert str(sample_tier.id) in sample_tenant.license_pools

    @pytest.mark.asyncio
    async def test_create_or_update_pool_updates_existing(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
    ):
        """Test updating an existing pool."""
        # Create initial pool
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        # Update pool
        pool = await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=20,
        )

        assert pool["total_count"] == 20
        assert pool["available_count"] == 20  # No assignments yet

    @pytest.mark.asyncio
    async def test_create_or_update_pool_cannot_reduce_below_assigned(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
    ):
        """Test that pool cannot be reduced below assigned count."""
        # Create pool and assign some licenses
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        # Manually set assigned count (simulating assignments)
        pools = sample_tenant.license_pools or {}
        pools[str(sample_tier.id)]["assigned_count"] = 5
        pools[str(sample_tier.id)]["available_count"] = 5
        sample_tenant.license_pools = pools
        session.add(sample_tenant)
        await session.commit()

        # Try to reduce below assigned
        with pytest.raises(ValueError, match="Cannot reduce pool below assigned"):
            await license_service.create_or_update_pool_for_tier(
                tenant_id=sample_tenant.id,
                tier_id=sample_tier.id,
                total_count=3,  # Less than 5 assigned
            )

    @pytest.mark.asyncio
    async def test_assign_license_to_user(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test assigning a license to a user."""
        # Create pool first
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        assigned_by = uuid4()
        user = await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=sample_tier.id,
            assigned_by=assigned_by,
        )

        assert user.license_is_active is True
        assert user.license_tier_id == sample_tier.id
        assert user.license_pool_id == sample_tier.id
        assert user.credits_allocated == sample_tier.default_credits
        assert user.credits_used == 0
        assert user.license_assigned_by == assigned_by

        # Verify pool counts updated
        await session.refresh(sample_tenant)
        pool = sample_tenant.license_pools[str(sample_tier.id)]
        assert pool["assigned_count"] == 1
        assert pool["available_count"] == 9

    @pytest.mark.asyncio
    async def test_assign_license_user_already_has_license(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test that user with active license cannot be assigned another."""
        # Create pool and assign license
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=sample_tier.id,
            assigned_by=uuid4(),
        )

        # Try to assign again
        with pytest.raises(ValueError, match="already has an active license"):
            await license_service.assign_license_to_user(
                user_id=sample_user.id,
                tier_id=sample_tier.id,
                assigned_by=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_assign_license_no_available_licenses(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test assigning when no licenses are available."""
        # Create pool with 0 available
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=0,
        )

        with pytest.raises(ValueError, match="No available licenses"):
            await license_service.assign_license_to_user(
                user_id=sample_user.id,
                tier_id=sample_tier.id,
                assigned_by=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_unassign_license_from_user(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test unassigning a license from a user."""
        # Create pool and assign license
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=sample_tier.id,
            assigned_by=uuid4(),
        )

        # Unassign
        user = await license_service.unassign_license_from_user(sample_user.id)

        assert user.license_is_active is False
        assert user.license_tier_id is None
        assert user.license_pool_id is None
        assert user.credits_allocated == 0
        assert user.credits_used == 0

        # Verify pool counts updated
        await session.refresh(sample_tenant)
        pool = sample_tenant.license_pools[str(sample_tier.id)]
        assert pool["assigned_count"] == 0
        assert pool["available_count"] == 10

    @pytest.mark.asyncio
    async def test_upgrade_user_license(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test upgrading a user's license."""
        # Create two tiers
        old_tier = sample_tier
        new_tier = LicenseTier(
            id=uuid4(),
            name="Enterprise",
            default_credits=50000,
            default_credits_per_month=5000,
            credits_per_usd=Decimal("500.00"),
            pricing_multiplier=Decimal("0.90"),
            is_active=True,
        )
        session.add(new_tier)
        await session.commit()

        # Create pools for both tiers
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=old_tier.id,
            total_count=10,
        )
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=new_tier.id,
            total_count=5,
        )

        # Assign old tier license
        await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=old_tier.id,
            assigned_by=uuid4(),
        )

        # Upgrade to new tier
        user = await license_service.upgrade_user_license(
            user_id=sample_user.id,
            new_tier_id=new_tier.id,
            assigned_by=uuid4(),
            preserve_credits=False,
        )

        assert user.license_tier_id == new_tier.id
        assert user.credits_allocated == new_tier.default_credits

        # Verify pool counts
        await session.refresh(sample_tenant)
        old_pool = sample_tenant.license_pools[str(old_tier.id)]
        new_pool = sample_tenant.license_pools[str(new_tier.id)]
        assert old_pool["assigned_count"] == 0
        assert old_pool["available_count"] == 10
        assert new_pool["assigned_count"] == 1
        assert new_pool["available_count"] == 4

    @pytest.mark.asyncio
    async def test_upgrade_license_preserve_credits(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test upgrading license with preserve_credits=True."""
        # Create new tier
        new_tier = LicenseTier(
            id=uuid4(),
            name="Enterprise",
            default_credits=50000,
            credits_per_usd=Decimal("500.00"),
            is_active=True,
        )
        session.add(new_tier)
        await session.commit()

        # Create pools
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=new_tier.id,
            total_count=5,
        )

        # Assign and use some credits
        await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=sample_tier.id,
            assigned_by=uuid4(),
        )
        sample_user.credits_used = 2000  # Use some credits
        session.add(sample_user)
        await session.commit()

        old_credits = sample_user.credits_allocated - sample_user.credits_used

        # Upgrade preserving credits
        user = await license_service.upgrade_user_license(
            user_id=sample_user.id,
            new_tier_id=new_tier.id,
            assigned_by=uuid4(),
            preserve_credits=True,
        )

        assert user.credits_allocated == old_credits + new_tier.default_credits

    @pytest.mark.asyncio
    async def test_deduct_credits(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test deducting credits from a user."""
        # Create pool and assign license
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=sample_tier.id,
            assigned_by=uuid4(),
        )

        # Deduct credits
        user = await license_service.deduct_credits(
            user_id=sample_user.id,
            credits=100,
            usage_record_id="trace_123",
            metadata={"model": "gpt-4"},
        )

        assert user.credits_used == 100
        assert user.credits_allocated - user.credits_used == sample_tier.default_credits - 100

        # Verify transaction created
        from sqlmodel import select

        stmt = select(TransactionTable).where(
            TransactionTable.user_id == sample_user.id,
            TransactionTable.transaction_type == "deduction",
        )
        result = await session.execute(stmt)
        transaction = result.scalars().first()
        assert transaction is not None
        assert transaction.credits_amount == 100
        assert transaction.usage_record_id == "trace_123"

    @pytest.mark.asyncio
    async def test_deduct_credits_insufficient(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test deducting more credits than available."""
        # Create pool and assign license
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=sample_tier.id,
            assigned_by=uuid4(),
        )

        # Try to deduct more than available
        with pytest.raises(ValueError, match="Insufficient credits"):
            await license_service.deduct_credits(
                user_id=sample_user.id,
                credits=sample_tier.default_credits + 1,
            )

    @pytest.mark.asyncio
    async def test_add_credits(
        self,
        license_service: LicenseService,
        session: AsyncSession,
        sample_tenant: Tenant,
        sample_tier: LicenseTier,
        sample_user: User,
    ):
        """Test adding credits to a user."""
        # Create pool and assign license
        await license_service.create_or_update_pool_for_tier(
            tenant_id=sample_tenant.id,
            tier_id=sample_tier.id,
            total_count=10,
        )

        await license_service.assign_license_to_user(
            user_id=sample_user.id,
            tier_id=sample_tier.id,
            assigned_by=uuid4(),
        )

        initial_credits = sample_user.credits_allocated

        # Add credits
        user = await license_service.add_credits(
            user_id=sample_user.id,
            credits=5000,
            created_by=uuid4(),
            metadata={"reason": "manual_topup"},
        )

        assert user.credits_allocated == initial_credits + 5000

        # Verify transaction created
        from sqlmodel import select

        stmt = select(TransactionTable).where(
            TransactionTable.user_id == sample_user.id,
            TransactionTable.transaction_type == "addition",
        )
        result = await session.execute(stmt)
        transaction = result.scalars().first()
        assert transaction is not None
        assert transaction.credits_amount == 5000

