"""Subscription service for managing tenant subscriptions."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from klx.log.logger import logger
from klx.services.deps import session_scope
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import select

from kluisz.schema.serialize import UUIDstr, str_to_uuid
from kluisz.services.base import Service
from kluisz.services.database.models.license_tier.model import LicenseTier
from kluisz.services.database.models.subscription.model import Subscription, SubscriptionCreate
from kluisz.services.database.models.subscription_history.model import (
    SubscriptionHistory,
    SubscriptionHistoryCreate,
)
from kluisz.services.database.models.tenant.model import Tenant
from kluisz.services.database.models.user.model import User


class SubscriptionService(Service):
    """Service for managing tenant subscriptions."""

    name = "subscription_service"

    async def create_subscription(
        self,
        tenant_id: UUIDstr,
        tier_id: UUIDstr,
        license_count: int,
        amount: Decimal,
        payment_method_id: str | None = None,
        created_by: UUIDstr | None = None,
    ) -> Subscription:
        """Create a new subscription for a tenant."""
        async with session_scope() as session:
            tenant = await session.get(Tenant, str_to_uuid(tenant_id))
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")

            tier = await session.get(LicenseTier, str_to_uuid(tier_id))
            if not tier:
                raise ValueError(f"License tier {tier_id} not found")

            now = datetime.now(timezone.utc)
            renewal_date = now + timedelta(days=30)

            subscription = Subscription(
                tenant_id=tenant_id,
                tier_id=tier_id,
                license_count=license_count,
                monthly_credits=tier.default_credits_per_month or 0,
                amount=amount,
                currency="USD",
                billing_cycle="monthly",
                status="active",
                start_date=now,
                renewal_date=renewal_date,
                next_payment_date=renewal_date,
                payment_method_id=payment_method_id,
            )

            # Update tenant subscription fields
            tenant.subscription_tier_id = tier_id
            tenant.subscription_license_count = license_count
            tenant.subscription_status = "active"
            tenant.subscription_start_date = now
            tenant.subscription_renewal_date = renewal_date
            tenant.subscription_amount = amount
            tenant.subscription_payment_method_id = payment_method_id

            # Create initial license pool
            pools = tenant.license_pools or {}
            tier_id_str = str(tier_id)
            pools[tier_id_str] = {
                "total_count": license_count,
                "available_count": license_count,
                "assigned_count": 0,
                "created_by": str(created_by) if created_by else None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
            tenant.license_pools = pools
            flag_modified(tenant, "license_pools")
            tenant.updated_at = now

            session.add(subscription)
            session.add(tenant)
            await session.commit()
            await session.refresh(subscription)

            # Create history entry
            history = SubscriptionHistory(
                subscription_id=subscription.id,
                tenant_id=tenant_id,
                action="created",
                new_tier_id=tier_id,
                new_license_count=license_count,
                new_amount=amount,
                changed_by=str_to_uuid(created_by) if created_by else None,
            )
            session.add(history)
            await session.commit()

            return subscription

    async def renew_subscription(self, subscription_id: UUIDstr) -> Subscription:
        """Renew a subscription for another month."""
        async with session_scope() as session:
            subscription = await session.get(Subscription, str_to_uuid(subscription_id))
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")

            if subscription.status != "active":
                raise ValueError(f"Subscription {subscription_id} is not active")

            now = datetime.now(timezone.utc)
            renewal_date = subscription.renewal_date + timedelta(days=30) if subscription.renewal_date else now + timedelta(days=30)

            subscription.last_payment_date = now
            subscription.next_payment_date = renewal_date
            subscription.renewal_date = renewal_date
            subscription.updated_at = now

            tenant = await session.get(Tenant, str_to_uuid(subscription.tenant_id))
            if tenant:
                tenant.subscription_renewal_date = renewal_date
                tenant.updated_at = now

                # Top up monthly credits for all active users
                stmt = select(User).where(
                    User.tenant_id == subscription.tenant_id,
                    User.license_is_active == True,  # noqa: E712
                    User.credits_per_month.isnot(None),
                )
                result = await session.execute(stmt)
                users = result.scalars().all()

                for user in users:
                    if user.credits_per_month:
                        user.credits_allocated = user.credits_allocated + user.credits_per_month
                        user.updated_at = now

            # Create history entry
            history = SubscriptionHistory(
                subscription_id=subscription_id,
                tenant_id=subscription.tenant_id,
                action="renewed",
                changed_by=None,  # System renewal
            )
            session.add(history)

            session.add(subscription)
            await session.commit()
            await session.refresh(subscription)

            return subscription

    async def cancel_subscription(
        self,
        subscription_id: UUIDstr,
        reason: str | None = None,
        cancelled_by: UUIDstr | None = None,
    ) -> Subscription:
        """Cancel a subscription."""
        async with session_scope() as session:
            subscription = await session.get(Subscription, str_to_uuid(subscription_id))
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")

            now = datetime.now(timezone.utc)

            subscription.status = "cancelled"
            subscription.cancelled_at = now
            subscription.end_date = subscription.renewal_date  # Access until end of paid period
            subscription.updated_at = now

            tenant = await session.get(Tenant, str_to_uuid(subscription.tenant_id))
            if tenant:
                tenant.subscription_status = "cancelled"
                tenant.subscription_end_date = subscription.end_date
                tenant.updated_at = now

            # Create history entry
            history = SubscriptionHistory(
                subscription_id=subscription_id,
                tenant_id=subscription.tenant_id,
                action="cancelled",
                reason=reason,
                changed_by=str_to_uuid(cancelled_by) if cancelled_by else None,
            )
            session.add(history)

            session.add(subscription)
            session.add(tenant)
            await session.commit()
            await session.refresh(subscription)

            return subscription

    async def teardown(self) -> None:
        """Teardown the service."""
        pass

