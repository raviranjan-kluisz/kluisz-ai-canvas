"""License service for managing license pools and user licenses."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from klx.log.logger import logger
from klx.services.deps import session_scope
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import select

from kluisz.schema.serialize import UUIDstr, str_to_uuid
from kluisz.services.base import Service
from kluisz.services.database.models.license_tier.model import LicenseTier
from kluisz.services.database.models.tenant.model import Tenant
from kluisz.services.database.models.transactions.model import TransactionTable
from kluisz.services.database.models.user.model import User


class LicenseService(Service):
    """Service for managing license pools and user licenses."""

    name = "license_service"

    async def get_tenant_license_pools(self, tenant_id: UUIDstr) -> dict[str, Any]:
        """Get all license pools for a tenant."""
        async with session_scope() as session:
            tenant = await session.get(Tenant, str_to_uuid(tenant_id))
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")
            return tenant.license_pools or {}

    async def create_or_update_pool_for_tier(
        self,
        tenant_id: UUIDstr,
        tier_id: UUIDstr,
        total_count: int,
        created_by: UUIDstr | None = None,
    ) -> dict[str, Any]:
        """Create or update a license pool for a specific tier."""
        async with session_scope() as session:
            tenant = await session.get(Tenant, str_to_uuid(tenant_id))
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")

            tier = await session.get(LicenseTier, str_to_uuid(tier_id))
            if not tier:
                raise ValueError(f"License tier {tier_id} not found")

            pools = tenant.license_pools or {}
            tier_id_str = str(tier_id)

            if tier_id_str in pools:
                # Update existing pool
                pool = pools[tier_id_str]
                current_assigned = pool.get("assigned_count", 0)
                if total_count < current_assigned:
                    raise ValueError(
                        f"Cannot reduce pool below assigned licenses ({current_assigned} assigned)"
                    )
                pool["total_count"] = total_count
                pool["available_count"] = total_count - current_assigned
                pool["updated_at"] = datetime.now(timezone.utc).isoformat()
            else:
                # Create new pool
                pools[tier_id_str] = {
                    "total_count": total_count,
                    "available_count": total_count,
                    "assigned_count": 0,
                    "created_by": str(created_by) if created_by else None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }

            tenant.license_pools = pools
            flag_modified(tenant, "license_pools")
            tenant.updated_at = datetime.now(timezone.utc)
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)

            return pools[tier_id_str]

    async def assign_license_to_user(
        self,
        user_id: UUIDstr,
        tier_id: UUIDstr,
        assigned_by: UUIDstr,
    ) -> User:
        """Assign a license from tenant's pool to a user."""
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")

            if not user.tenant_id:
                raise ValueError(f"User {user_id} has no tenant")

            if user.license_is_active:
                raise ValueError(f"User {user_id} already has an active license")

            tier = await session.get(LicenseTier, str_to_uuid(tier_id))
            if not tier:
                raise ValueError(f"License tier {tier_id} not found")

            tenant = await session.get(Tenant, str_to_uuid(user.tenant_id))
            if not tenant:
                raise ValueError(f"Tenant {user.tenant_id} not found")

            pools = tenant.license_pools or {}
            tier_id_str = str(tier_id)

            if tier_id_str not in pools:
                raise ValueError(f"No license pool found for tier {tier_id}")

            pool = pools[tier_id_str]
            available = pool.get("available_count", 0)

            if available <= 0:
                raise ValueError(f"No available licenses in pool for tier {tier_id}")

            # Update pool counts
            pool["available_count"] = available - 1
            pool["assigned_count"] = pool.get("assigned_count", 0) + 1
            pool["updated_at"] = datetime.now(timezone.utc).isoformat()
            tenant.license_pools = pools
            flag_modified(tenant, "license_pools")
            tenant.updated_at = datetime.now(timezone.utc)

            # Update user with license
            user.license_pool_id = tier_id
            user.license_tier_id = tier_id
            user.credits_allocated = tier.default_credits
            user.credits_used = 0
            user.credits_per_month = tier.default_credits_per_month
            user.license_is_active = True
            user.license_assigned_at = datetime.now(timezone.utc)
            user.license_assigned_by = str_to_uuid(assigned_by) if assigned_by else None
            user.updated_at = datetime.now(timezone.utc)

            session.add(tenant)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            return user

    async def unassign_license_from_user(self, user_id: UUIDstr) -> User:
        """Unassign license from a user and return it to the pool."""
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")

            if not user.license_is_active or not user.license_tier_id:
                raise ValueError(f"User {user_id} has no active license to unassign")

            if not user.tenant_id:
                raise ValueError(f"User {user_id} has no tenant")

            tenant = await session.get(Tenant, str_to_uuid(user.tenant_id))
            if not tenant:
                raise ValueError(f"Tenant {user.tenant_id} not found")

            tier_id_str = str(user.license_tier_id)
            pools = tenant.license_pools or {}

            if tier_id_str in pools:
                pool = pools[tier_id_str]
                pool["available_count"] = pool.get("available_count", 0) + 1
                pool["assigned_count"] = max(0, pool.get("assigned_count", 0) - 1)
                pool["updated_at"] = datetime.now(timezone.utc).isoformat()
                tenant.license_pools = pools
                flag_modified(tenant, "license_pools")
                tenant.updated_at = datetime.now(timezone.utc)
                session.add(tenant)

            # Clear user license fields
            user.license_pool_id = None
            user.license_tier_id = None
            user.credits_allocated = 0
            user.credits_used = 0
            user.credits_per_month = None
            user.license_is_active = False
            user.license_assigned_at = None
            user.license_assigned_by = None
            user.license_expires_at = None
            user.updated_at = datetime.now(timezone.utc)

            session.add(user)
            await session.commit()
            await session.refresh(user)

            return user

    async def upgrade_user_license(
        self,
        user_id: UUIDstr,
        new_tier_id: UUIDstr,
        assigned_by: UUIDstr,
        preserve_credits: bool = False,
    ) -> User:
        """Upgrade user license to a new tier."""
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")

            if not user.license_is_active:
                raise ValueError(f"User {user_id} has no active license to upgrade")

            if not user.tenant_id:
                raise ValueError(f"User {user_id} has no tenant")

            old_tier_id = user.license_tier_id
            if not old_tier_id:
                raise ValueError(f"User {user_id} has no current tier")

            new_tier = await session.get(LicenseTier, str_to_uuid(new_tier_id))
            if not new_tier:
                raise ValueError(f"License tier {new_tier_id} not found")

            tenant = await session.get(Tenant, str_to_uuid(user.tenant_id))
            if not tenant:
                raise ValueError(f"Tenant {user.tenant_id} not found")

            pools = tenant.license_pools or {}
            new_tier_id_str = str(new_tier_id)

            if new_tier_id_str not in pools:
                raise ValueError(f"No license pool found for tier {new_tier_id}")

            pool = pools[new_tier_id_str]
            if pool.get("available_count", 0) <= 0:
                raise ValueError(f"No available licenses in pool for tier {new_tier_id}")

            # Unassign from old tier pool
            old_tier_id_str = str(old_tier_id)
            if old_tier_id_str in pools:
                old_pool = pools[old_tier_id_str]
                old_pool["available_count"] = old_pool.get("available_count", 0) + 1
                old_pool["assigned_count"] = max(0, old_pool.get("assigned_count", 0) - 1)
                old_pool["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Assign to new tier pool
            pool["available_count"] = pool.get("available_count", 0) - 1
            pool["assigned_count"] = pool.get("assigned_count", 0) + 1
            pool["updated_at"] = datetime.now(timezone.utc).isoformat()

            tenant.license_pools = pools
            flag_modified(tenant, "license_pools")
            tenant.updated_at = datetime.now(timezone.utc)

            # Update user license
            old_credits = user.credits_allocated
            if preserve_credits:
                # Preserve remaining credits (allocated - used) and add new tier's credits
                remaining_credits = user.credits_allocated - user.credits_used
                user.credits_allocated = remaining_credits + new_tier.default_credits
                user.credits_used = 0  # Reset used credits since we're adding remaining to allocated
            else:
                user.credits_allocated = new_tier.default_credits
                user.credits_used = 0

            user.license_pool_id = new_tier_id
            user.license_tier_id = new_tier_id
            user.credits_per_month = new_tier.default_credits_per_month
            user.license_assigned_at = datetime.now(timezone.utc)
            user.license_assigned_by = str_to_uuid(assigned_by) if assigned_by else None
            user.updated_at = datetime.now(timezone.utc)

            # Log upgrade transaction
            transaction = TransactionTable(
                user_id=str_to_uuid(user_id),
                transaction_type="upgrade",
                credits_amount=new_tier.default_credits,
                credits_before=old_credits,
                credits_after=user.credits_allocated,
                transaction_metadata={
                    "old_tier_id": str(old_tier_id),
                    "new_tier_id": str(new_tier_id),
                    "preserve_credits": preserve_credits,
                },
                created_by=str_to_uuid(assigned_by) if assigned_by else None,
            )

            session.add(tenant)
            session.add(user)
            session.add(transaction)
            await session.commit()
            await session.refresh(user)

            return user

    async def deduct_credits(
        self,
        user_id: UUIDstr,
        credits: int,
        usage_record_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> User:
        """Deduct credits from user and create transaction record."""
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")

            if not user.license_is_active:
                raise ValueError(f"User {user_id} has no active license")

            credits_remaining = user.credits_allocated - user.credits_used
            if credits_remaining < credits:
                raise ValueError(
                    f"Insufficient credits: {credits_remaining} remaining, {credits} requested"
                )

            credits_before = credits_remaining
            user.credits_used = user.credits_used + credits
            user.updated_at = datetime.now(timezone.utc)
            credits_after = user.credits_allocated - user.credits_used

            # Create transaction record
            transaction = TransactionTable(
                user_id=str_to_uuid(user_id),
                transaction_type="deduction",
                credits_amount=credits,
                credits_before=credits_before,
                credits_after=credits_after,
                usage_record_id=usage_record_id,
                transaction_metadata=metadata or {},
                created_by=str_to_uuid(user_id),
            )

            session.add(user)
            session.add(transaction)
            await session.commit()
            await session.refresh(user)

            return user

    async def add_credits(
        self,
        user_id: UUIDstr,
        credits: int,
        created_by: UUIDstr | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> User:
        """Add credits to user and create transaction record."""
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            if not user:
                raise ValueError(f"User {user_id} not found")

            credits_before = user.credits_allocated - user.credits_used
            user.credits_allocated = user.credits_allocated + credits
            user.updated_at = datetime.now(timezone.utc)
            credits_after = user.credits_allocated - user.credits_used

            # Create transaction record
            transaction = TransactionTable(
                user_id=str_to_uuid(user_id),
                transaction_type="addition",
                credits_amount=credits,
                credits_before=credits_before,
                credits_after=credits_after,
                transaction_metadata=metadata or {},
                created_by=str_to_uuid(created_by) if created_by else str_to_uuid(user_id),
            )

            session.add(user)
            session.add(transaction)
            await session.commit()
            await session.refresh(user)

            return user

    async def teardown(self) -> None:
        """Teardown the service."""
        pass

