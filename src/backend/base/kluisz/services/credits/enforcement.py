"""Credit enforcement service for controlling flow execution based on credits.

This service:
1. Checks if a user has sufficient credits before flow execution
2. Provides credit status information

Note: Credit DEDUCTION is now handled by the KluiszMeteringCallback in real-time
during flow execution. This service only handles PRE-execution checks.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from klx.log.logger import logger
from klx.services.deps import session_scope
from sqlmodel import select, func, and_

from kluisz.schema.serialize import UUIDstr, str_to_uuid
from kluisz.services.base import Service


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have sufficient credits."""
    
    def __init__(
        self,
        user_id: str,
        credits_required: int = 0,
        credits_remaining: int = 0,
        message: str | None = None,
    ):
        self.user_id = user_id
        self.credits_required = credits_required
        self.credits_remaining = credits_remaining
        self.message = message or (
            f"Insufficient credits: {credits_remaining} remaining, "
            f"approximately {credits_required} required"
        )
        super().__init__(self.message)


class NoActiveLicenseError(Exception):
    """Raised when user doesn't have an active license."""
    
    def __init__(self, user_id: str, message: str | None = None):
        self.user_id = user_id
        self.message = message or f"User {user_id} does not have an active license"
        super().__init__(self.message)


class CreditEnforcementService(Service):
    """Service for enforcing credit limits on flow execution.
    
    Pre-execution checks:
    - Check if user has an active license
    - Check if user has sufficient credits (with optional estimation)
    
    Note: Credit deduction is handled by KluiszMeteringCallback during flow execution.
    This service only handles pre-execution checks and credit status queries.
    """

    name = "credit_enforcement_service"

    def __init__(self):
        # Minimum credits required to start a flow (configurable)
        self.min_credits_to_start = 1

    async def check_user_can_execute(
        self,
        user_id: UUIDstr,
        *,
        estimated_credits: int | None = None,
    ) -> dict[str, Any]:
        """Check if user can execute a flow.
        
        Args:
            user_id: User ID
            estimated_credits: Optional estimated credits required
        
        Returns:
            Dict with credits info and can_execute status
        
        Raises:
            NoActiveLicenseError: If user doesn't have an active license
            InsufficientCreditsError: If user doesn't have enough credits
        """
        from kluisz.services.database.models.user.model import User
        
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Platform superadmins bypass credit checks
            if user.is_platform_superadmin:
                return {
                    "can_execute": True,
                    "is_superadmin": True,
                    "message": "Super admins have unlimited execution",
                }
            
            # Check for active license
            if not user.license_is_active:
                raise NoActiveLicenseError(
                    user_id=str(user_id),
                    message="You need an active license to execute flows"
                )
            
            # Calculate remaining credits
            credits_allocated = user.credits_allocated or 0
            credits_used = user.credits_used or 0
            credits_remaining = credits_allocated - credits_used
            
            # Determine credits required
            credits_required = estimated_credits or self.min_credits_to_start
            
            # Check if user has enough credits
            if credits_remaining < credits_required:
                raise InsufficientCreditsError(
                    user_id=str(user_id),
                    credits_required=credits_required,
                    credits_remaining=credits_remaining,
                )
            
            return {
                "can_execute": True,
                "credits_allocated": credits_allocated,
                "credits_used": credits_used,
                "credits_remaining": credits_remaining,
                "credits_required": credits_required,
                "license_tier_id": str(user.license_tier_id) if user.license_tier_id else None,
            }

    async def estimate_credits_for_flow(
        self,
        flow_id: UUIDstr,
        user_id: UUIDstr,
    ) -> int:
        """Estimate credits required for a flow based on historical usage.
        
        Uses local transaction data (from metering callback) to calculate average.
        
        Args:
            flow_id: Flow ID
            user_id: User ID (for tier-specific pricing)
        
        Returns:
            Estimated credits required
        """
        from kluisz.services.database.models.transactions.model import TransactionTable
        
        try:
            async with session_scope() as session:
                # Get recent transactions for this flow
                stmt = select(TransactionTable).where(
                    and_(
                        TransactionTable.flow_id == str_to_uuid(flow_id),
                        TransactionTable.transaction_type == "deduction",
                    )
                ).order_by(TransactionTable.timestamp.desc()).limit(10)
                
                result = await session.exec(stmt)
                transactions = list(result.all())
                
                if not transactions:
                    return self.min_credits_to_start
                
                # Calculate average credits from recent executions
                total_credits = sum(tx.credits_amount or 0 for tx in transactions)
                avg_credits = total_credits // len(transactions)
                
                # Return at least minimum
                return max(avg_credits, self.min_credits_to_start)
                
        except Exception as e:
            logger.warning(f"Error estimating credits for flow {flow_id}: {e}")
            return self.min_credits_to_start

    async def get_user_credit_status(self, user_id: UUIDstr) -> dict[str, Any]:
        """Get current credit status for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with credit status information
        """
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.license_tier.model import LicenseTier
        
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            credits_allocated = user.credits_allocated or 0
            credits_used = user.credits_used or 0
            credits_remaining = credits_allocated - credits_used
            
            # Calculate usage percentage
            usage_percent = 0
            if credits_allocated > 0:
                usage_percent = round((credits_used / credits_allocated) * 100, 1)
            
            tier_info = None
            if user.license_tier_id:
                tier = await session.get(LicenseTier, user.license_tier_id)
                if tier:
                    tier_info = {
                        "id": str(tier.id),
                        "name": tier.name,
                        "credits_per_usd": float(tier.credits_per_usd or 0),
                        "default_credits": tier.default_credits or 0,
                    }
            
            return {
                "user_id": str(user_id),
                "username": user.username,
                "credits_allocated": credits_allocated,
                "credits_used": credits_used,
                "credits_remaining": credits_remaining,
                "credits_per_month": user.credits_per_month,
                "usage_percent": usage_percent,
                "license_is_active": user.license_is_active,
                "license_tier": tier_info,
                "can_execute": user.license_is_active and credits_remaining > 0,
                "is_low_credits": credits_remaining < (credits_allocated * 0.2) if credits_allocated > 0 else False,
                "is_out_of_credits": credits_remaining <= 0,
            }

    async def refund_credits(
        self,
        user_id: UUIDstr,
        credits: int,
        reason: str,
        refunded_by: UUIDstr | None = None,
    ) -> dict[str, Any]:
        """Refund credits to a user.
        
        Args:
            user_id: User ID
            credits: Credits to refund
            reason: Reason for refund
            refunded_by: ID of user/admin doing the refund
        
        Returns:
            Dict with refund details
        """
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.transactions.model import TransactionTable
        
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            credits_before = (user.credits_allocated or 0) - (user.credits_used or 0)
            
            # Refund by reducing credits_used
            user.credits_used = max(0, (user.credits_used or 0) - credits)
            user.updated_at = datetime.now(timezone.utc)
            
            credits_after = (user.credits_allocated or 0) - (user.credits_used or 0)
            
            # Create transaction record
            transaction = TransactionTable(
                id=uuid4(),
                user_id=str_to_uuid(user_id),
                transaction_type="refund",
                credits_amount=credits,
                credits_before=credits_before,
                credits_after=credits_after,
                transaction_metadata={
                    "reason": reason,
                    "refunded_by": str(refunded_by) if refunded_by else None,
                },
                created_by=str_to_uuid(refunded_by) if refunded_by else str_to_uuid(user_id),
                created_at=datetime.now(timezone.utc),
            )
            
            session.add(user)
            session.add(transaction)
            await session.commit()
            
            logger.info(f"Refunded {credits} credits to user {user_id}: {reason}")
            
            return {
                "credits_refunded": credits,
                "credits_before": credits_before,
                "credits_after": credits_after,
                "transaction_id": str(transaction.id),
            }

    async def teardown(self) -> None:
        """Cleanup resources."""
        pass


# Global instance for easy access
_credit_enforcement_service: CreditEnforcementService | None = None


def get_credit_enforcement_service() -> CreditEnforcementService:
    """Get the global credit enforcement service instance."""
    global _credit_enforcement_service
    if _credit_enforcement_service is None:
        _credit_enforcement_service = CreditEnforcementService()
    return _credit_enforcement_service
