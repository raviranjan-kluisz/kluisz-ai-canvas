"""Usage tracking service - DEPRECATED.

This service is deprecated. Analytics and usage tracking now use the transaction
table directly, which is populated in real-time by the KluiszMeteringCallback.

See:
- kluisz.services.analytics.service.AnalyticsService for analytics queries
- kluisz.services.tracing.metering_callback.KluiszMeteringCallback for real-time metering
- kluisz.api.v1.billing for billing endpoints
"""

import warnings

warnings.warn(
    "UsageTracker is deprecated. Use AnalyticsService for analytics queries.",
    DeprecationWarning,
    stacklevel=2,
)


class UsageTracker:
    """DEPRECATED: Usage tracking service.
    
    This class is deprecated. All usage tracking is now done via:
    1. KluiszMeteringCallback - captures usage in real-time during flow execution
    2. TransactionTable - stores all usage data
    3. AnalyticsService - provides analytics queries
    
    Do not use this class for new code.
    """
    
    @staticmethod
    async def track_flow_run(*args, **kwargs):
        """DEPRECATED: Flow runs are now tracked by metering callback."""
        pass
    
    @staticmethod
    async def track_api_call(*args, **kwargs):
        """DEPRECATED: API calls are tracked by metering callback."""
        pass
    
    @staticmethod
    async def track_storage(*args, **kwargs):
        """DEPRECATED: Storage tracking not currently implemented."""
        pass
    
    @staticmethod
    async def get_user_usage(*args, **kwargs):
        """DEPRECATED: Use AnalyticsService.get_user_dashboard_data()."""
        return []
    
    @staticmethod
    async def get_tenant_usage(*args, **kwargs):
        """DEPRECATED: Use AnalyticsService.get_tenant_dashboard_data()."""
        return []
    
    @staticmethod
    async def get_user_usage_summary(*args, **kwargs):
        """DEPRECATED: Use AnalyticsService.get_user_dashboard_data()."""
        return {}
    
    @staticmethod
    async def get_tenant_usage_summary(*args, **kwargs):
        """DEPRECATED: Use AnalyticsService.get_tenant_dashboard_data()."""
        return {}
