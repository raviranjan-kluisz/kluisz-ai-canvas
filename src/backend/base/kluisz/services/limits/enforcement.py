"""Limits enforcement service for controlling resource usage based on license tier.

This service enforces:
1. max_flows - Maximum number of flows a user can create
2. max_api_calls - Maximum API calls per billing period
3. max_concurrent_executions - (future) Maximum concurrent flow executions

Note: Credits enforcement is handled separately by CreditEnforcementService.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from klx.log.logger import logger
from klx.services.deps import session_scope
from sqlmodel import select, func, and_

from kluisz.schema.serialize import UUIDstr, str_to_uuid
from kluisz.services.base import Service


class FlowLimitExceededError(Exception):
    """Raised when user has reached their flow limit."""
    
    def __init__(
        self,
        user_id: str,
        current_count: int,
        max_allowed: int,
        message: str | None = None,
    ):
        self.user_id = user_id
        self.current_count = current_count
        self.max_allowed = max_allowed
        self.message = message or (
            f"Flow limit reached: {current_count}/{max_allowed} flows. "
            "Please delete some flows or upgrade your plan."
        )
        super().__init__(self.message)


class ApiCallLimitExceededError(Exception):
    """Raised when user has reached their API call limit for the billing period."""
    
    def __init__(
        self,
        user_id: str,
        current_count: int,
        max_allowed: int,
        message: str | None = None,
    ):
        self.user_id = user_id
        self.current_count = current_count
        self.max_allowed = max_allowed
        self.message = message or (
            f"API call limit reached: {current_count}/{max_allowed} calls this period. "
            "Please wait for your limit to reset or upgrade your plan."
        )
        super().__init__(self.message)


class LimitsEnforcementService(Service):
    """Service for enforcing resource limits based on license tier.
    
    Limits checked:
    - max_flows: Total flows a user can create
    - max_api_calls: API calls per billing period (counted from transactions)
    """

    name = "limits_enforcement_service"

    async def check_can_create_flow(self, user_id: UUIDstr) -> dict[str, Any]:
        """Check if user can create a new flow.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with current count, limit, and can_create status
        
        Raises:
            FlowLimitExceededError: If user has reached their flow limit
        """
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.license_tier.model import LicenseTier
        from kluisz.services.database.models.flow.model import Flow
        
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Platform superadmins have unlimited flows
            if user.is_platform_superadmin:
                return {
                    "can_create": True,
                    "is_superadmin": True,
                    "message": "Super admins have unlimited flows",
                }
            
            # Get user's license tier
            if not user.license_tier_id:
                # No license = no limit enforcement (or could default to strict)
                return {
                    "can_create": True,
                    "current_count": 0,
                    "max_allowed": None,
                    "message": "No license tier - no limit enforced",
                }
            
            tier = await session.get(LicenseTier, user.license_tier_id)
            if not tier:
                return {
                    "can_create": True,
                    "current_count": 0,
                    "max_allowed": None,
                    "message": "License tier not found - no limit enforced",
                }
            
            # None means unlimited
            if tier.max_flows is None:
                return {
                    "can_create": True,
                    "current_count": 0,
                    "max_allowed": None,
                    "unlimited": True,
                    "message": "Unlimited flows",
                }
            
            # Count user's current flows
            current_count = await session.scalar(
                select(func.count(Flow.id)).where(Flow.user_id == user.id)
            ) or 0
            
            # Check limit
            if current_count >= tier.max_flows:
                raise FlowLimitExceededError(
                    user_id=str(user_id),
                    current_count=current_count,
                    max_allowed=tier.max_flows,
                )
            
            return {
                "can_create": True,
                "current_count": current_count,
                "max_allowed": tier.max_flows,
                "remaining": tier.max_flows - current_count,
                "tier_name": tier.name,
            }

    async def check_api_call_limit(self, user_id: UUIDstr) -> dict[str, Any]:
        """Check if user can make another API call (flow execution).
        
        API calls are counted from the transactions table for the current billing period.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with current count, limit, and can_execute status
        
        Raises:
            ApiCallLimitExceededError: If user has reached their API call limit
        """
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.license_tier.model import LicenseTier
        from kluisz.services.database.models.transactions.model import TransactionTable
        
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Platform superadmins have unlimited API calls
            if user.is_platform_superadmin:
                return {
                    "can_execute": True,
                    "is_superadmin": True,
                    "message": "Super admins have unlimited API calls",
                }
            
            # Get user's license tier
            if not user.license_tier_id:
                return {
                    "can_execute": True,
                    "current_count": 0,
                    "max_allowed": None,
                    "message": "No license tier - no limit enforced",
                }
            
            tier = await session.get(LicenseTier, user.license_tier_id)
            if not tier:
                return {
                    "can_execute": True,
                    "current_count": 0,
                    "max_allowed": None,
                    "message": "License tier not found - no limit enforced",
                }
            
            # None means unlimited
            if tier.max_api_calls is None:
                return {
                    "can_execute": True,
                    "current_count": 0,
                    "max_allowed": None,
                    "unlimited": True,
                    "message": "Unlimited API calls",
                }
            
            # Count API calls for current billing period (month)
            # We count transactions with type="deduction" for this user this month
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            
            current_count = await session.scalar(
                select(func.count(TransactionTable.id)).where(
                    and_(
                        TransactionTable.user_id == user.id,
                        TransactionTable.transaction_type == "deduction",
                        TransactionTable.timestamp >= start_of_month,
                    )
                )
            ) or 0
            
            # Check limit
            if current_count >= tier.max_api_calls:
                raise ApiCallLimitExceededError(
                    user_id=str(user_id),
                    current_count=current_count,
                    max_allowed=tier.max_api_calls,
                )
            
            return {
                "can_execute": True,
                "current_count": current_count,
                "max_allowed": tier.max_api_calls,
                "remaining": tier.max_api_calls - current_count,
                "tier_name": tier.name,
                "period_start": start_of_month.isoformat(),
            }

    async def get_user_limits_status(self, user_id: UUIDstr) -> dict[str, Any]:
        """Get comprehensive limits status for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with all limit statuses
        """
        from kluisz.services.database.models.user.model import User
        from kluisz.services.database.models.license_tier.model import LicenseTier
        from kluisz.services.database.models.flow.model import Flow
        from kluisz.services.database.models.transactions.model import TransactionTable
        
        async with session_scope() as session:
            user = await session.get(User, str_to_uuid(user_id))
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            result: dict[str, Any] = {
                "user_id": str(user_id),
                "is_superadmin": user.is_platform_superadmin,
            }
            
            if user.is_platform_superadmin:
                result["message"] = "Super admins have unlimited resources"
                return result
            
            # Get tier info
            tier = None
            if user.license_tier_id:
                tier = await session.get(LicenseTier, user.license_tier_id)
            
            # Flow count
            flow_count = await session.scalar(
                select(func.count(Flow.id)).where(Flow.user_id == user.id)
            ) or 0
            
            # API calls this month
            now = datetime.now(timezone.utc)
            start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            
            api_call_count = await session.scalar(
                select(func.count(TransactionTable.id)).where(
                    and_(
                        TransactionTable.user_id == user.id,
                        TransactionTable.transaction_type == "deduction",
                        TransactionTable.timestamp >= start_of_month,
                    )
                )
            ) or 0
            
            # Build limits info
            result["flows"] = {
                "current": flow_count,
                "max": tier.max_flows if tier else None,
                "unlimited": tier is None or tier.max_flows is None,
                "remaining": (tier.max_flows - flow_count) if tier and tier.max_flows else None,
                "percent_used": round(flow_count / tier.max_flows * 100, 1) if tier and tier.max_flows else 0,
            }
            
            result["api_calls"] = {
                "current": api_call_count,
                "max": tier.max_api_calls if tier else None,
                "unlimited": tier is None or tier.max_api_calls is None,
                "remaining": (tier.max_api_calls - api_call_count) if tier and tier.max_api_calls else None,
                "period_start": start_of_month.isoformat(),
                "percent_used": round(api_call_count / tier.max_api_calls * 100, 1) if tier and tier.max_api_calls else 0,
            }
            
            if tier:
                result["tier"] = {
                    "id": str(tier.id),
                    "name": tier.name,
                }
            
            return result

    async def teardown(self) -> None:
        """Cleanup resources."""
        pass


# Global instance for easy access
_limits_enforcement_service: LimitsEnforcementService | None = None


def get_limits_enforcement_service() -> LimitsEnforcementService:
    """Get the global limits enforcement service instance."""
    global _limits_enforcement_service
    if _limits_enforcement_service is None:
        _limits_enforcement_service = LimitsEnforcementService()
    return _limits_enforcement_service




