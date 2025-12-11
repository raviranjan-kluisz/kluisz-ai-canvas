"""Langfuse client service for fetching analytics and trace data."""

import os
from datetime import datetime
from decimal import Decimal
from typing import Any

from klx.log.logger import logger

from kluisz.schema.serialize import UUIDstr
from kluisz.services.base import Service


class LangfuseClientService(Service):
    """Service for fetching analytics and trace data from Langfuse.
    
    Uses the Langfuse SDK to retrieve:
    - Traces with usage data (tokens, cost)
    - Aggregated statistics by tenant, user, flow
    - Time-series analytics data
    """

    name = "langfuse_client_service"

    def __init__(self):
        self._client = None
        self._ready = False
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the Langfuse client."""
        try:
            from langfuse import Langfuse
            
            config = self._get_config()
            if not config:
                logger.warning("Langfuse not configured - analytics will be unavailable")
                return
            
            self._client = Langfuse(**config)
            
            # Test connection
            try:
                from langfuse.api.core.request_options import RequestOptions
                self._client.client.health.health(request_options=RequestOptions(timeout_in_seconds=3))
                self._ready = True
                logger.info("Langfuse client initialized successfully")
            except Exception as e:
                logger.warning(f"Langfuse connection test failed: {e}")
                self._ready = False
                
        except ImportError:
            logger.warning("Langfuse SDK not installed. Install with: pip install langfuse")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}")

    @staticmethod
    def _get_config() -> dict | None:
        """Get Langfuse configuration from environment variables.
        
        Supports both KLUISZ_LANGFUSE_* and LANGFUSE_* prefixes for backwards compatibility.
        Also supports both HOST and BASE_URL variants.
        """
        secret_key = os.getenv("KLUISZ_LANGFUSE_SECRET_KEY") or os.getenv("LANGFUSE_SECRET_KEY")
        public_key = os.getenv("KLUISZ_LANGFUSE_PUBLIC_KEY") or os.getenv("LANGFUSE_PUBLIC_KEY")
        # Support both HOST and BASE_URL (BASE_URL takes precedence)
        host = (
            os.getenv("KLUISZ_LANGFUSE_BASE_URL") or 
            os.getenv("KLUISZ_LANGFUSE_HOST") or 
            os.getenv("LANGFUSE_BASE_URL") or 
            os.getenv("LANGFUSE_HOST")
        )
        
        if secret_key and public_key and host:
            return {"secret_key": secret_key, "public_key": public_key, "host": host}
        return None

    @property
    def ready(self) -> bool:
        """Check if the Langfuse client is ready."""
        return self._ready and self._client is not None

    # Langfuse API max limit is 100
    MAX_LIMIT = 100
    
    async def get_traces(
        self,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        kluisz_project_id: str | None = None,
        kluisz_flow_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Fetch traces from Langfuse with optional filters.
        
        Args:
            tenant_id: Filter by tenant ID (from trace metadata)
            user_id: Filter by user ID
            kluisz_project_id: Filter by Kluisz project/folder ID (from trace metadata)
            kluisz_flow_id: Filter by Kluisz flow ID (from trace metadata)
            start_date: Filter traces from this date
            end_date: Filter traces until this date
            limit: Maximum number of traces to return (max 100 per Langfuse API)
            page: Page number for pagination (1-based)
        
        Returns:
            List of trace dictionaries with usage data
        """
        if not self.ready:
            logger.warning("Langfuse client not ready - returning empty traces")
            return []
        
        try:
            # Langfuse API has a max limit of 100
            actual_limit = min(limit, self.MAX_LIMIT)
            
            # Build filter parameters - Langfuse SDK uses page, not offset
            params: dict[str, Any] = {
                "limit": actual_limit,
                "page": page,
            }
            
            if user_id:
                params["user_id"] = user_id
            if start_date:
                params["from_timestamp"] = start_date
            if end_date:
                params["to_timestamp"] = end_date
            
            # Fetch traces using the SDK
            traces_response = self._client.fetch_traces(**params)
            traces = []
            
            for trace in traces_response.data:
                trace_dict = self._trace_to_dict(trace)
                
                # Filter by metadata fields if specified
                metadata = trace_dict.get("metadata", {})
                
                if tenant_id and metadata.get("tenant_id") != tenant_id:
                    continue
                if kluisz_project_id and metadata.get("kluisz_project_id") != kluisz_project_id:
                    continue
                if kluisz_flow_id and metadata.get("kluisz_flow_id") != kluisz_flow_id:
                    continue
                
                traces.append(trace_dict)
            
            return traces
            
        except Exception as e:
            logger.error(f"Error fetching traces from Langfuse: {e}")
            return []
    
    async def get_all_traces(
        self,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        kluisz_project_id: str | None = None,
        kluisz_flow_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        max_traces: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch all traces with pagination (up to max_traces).
        
        Args:
            tenant_id: Filter by tenant ID (from trace metadata)
            user_id: Filter by user ID
            kluisz_project_id: Filter by Kluisz project/folder ID (from trace metadata)
            kluisz_flow_id: Filter by Kluisz flow ID (from trace metadata)
            start_date: Filter traces from this date
            end_date: Filter traces until this date
            max_traces: Maximum total traces to fetch across all pages
        
        Returns:
            List of trace dictionaries with usage data
        """
        all_traces: list[dict[str, Any]] = []
        page = 1
        max_pages = (max_traces // self.MAX_LIMIT) + 1
        
        while len(all_traces) < max_traces and page <= max_pages:
            traces = await self.get_traces(
                tenant_id=tenant_id,
                user_id=user_id,
                kluisz_project_id=kluisz_project_id,
                kluisz_flow_id=kluisz_flow_id,
                start_date=start_date,
                end_date=end_date,
                limit=self.MAX_LIMIT,
                page=page,
            )
            
            if not traces:
                break  # No more data
            
            all_traces.extend(traces)
            
            if len(traces) < self.MAX_LIMIT:
                break  # Last page
            
            page += 1
        
        return all_traces[:max_traces]

    def _trace_to_dict(self, trace: Any) -> dict[str, Any]:
        """Convert a Langfuse trace object to a dictionary."""
        try:
            trace_dict = {
                "id": str(trace.id) if trace.id else None,
                "name": trace.name,
                "user_id": trace.user_id,
                "session_id": trace.session_id,
                "metadata": trace.metadata or {},
                "timestamp": trace.timestamp,
                "input": trace.input,
                "output": trace.output,
                "status": getattr(trace, "status", None),
                "level": getattr(trace, "level", None),
                "latency": getattr(trace, "latency", None),  # Duration in seconds
            }
            
            # Extract usage data (tokens and cost)
            usage = {}
            if hasattr(trace, "usage"):
                usage_obj = trace.usage
                if usage_obj:
                    usage = {
                        "totalTokens": getattr(usage_obj, "total_tokens", 0) or getattr(usage_obj, "totalTokens", 0) or 0,
                        "inputTokens": getattr(usage_obj, "input_tokens", 0) or getattr(usage_obj, "inputTokens", 0) or 0,
                        "outputTokens": getattr(usage_obj, "output_tokens", 0) or getattr(usage_obj, "outputTokens", 0) or 0,
                        "totalCost": getattr(usage_obj, "total_cost", 0) or getattr(usage_obj, "totalCost", 0) or 0,
                    }
            
            # Try alternative cost locations
            if not usage.get("totalCost"):
                usage["totalCost"] = (
                    getattr(trace, "total_cost", 0) or
                    getattr(trace, "totalCost", 0) or
                    getattr(trace, "cost", 0) or
                    0
                )
            
            trace_dict["usage"] = usage
            
            return trace_dict
            
        except Exception as e:
            logger.error(f"Error converting trace to dict: {e}")
            return {}

    async def get_trace_by_id(self, trace_id: str) -> dict[str, Any] | None:
        """Fetch a single trace by ID."""
        if not self.ready:
            return None
        
        try:
            trace = self._client.fetch_trace(trace_id)
            return self._trace_to_dict(trace) if trace else None
        except Exception as e:
            logger.error(f"Error fetching trace {trace_id}: {e}")
            return None

    async def get_sessions(
        self,
        *,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch sessions from Langfuse."""
        if not self.ready:
            return []
        
        try:
            params: dict[str, Any] = {"limit": limit}
            
            if start_date:
                params["from_timestamp"] = start_date
            if end_date:
                params["to_timestamp"] = end_date
            
            sessions_response = self._client.fetch_sessions(**params)
            sessions = []
            
            for session in sessions_response.data:
                session_dict = {
                    "id": str(session.id) if session.id else None,
                    "created_at": getattr(session, "created_at", None),
                    "user_id": getattr(session, "user_id", None),
                }
                
                # Filter by user_id if specified
                if user_id and session_dict.get("user_id") != user_id:
                    continue
                
                sessions.append(session_dict)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error fetching sessions: {e}")
            return []

    async def get_aggregated_usage(
        self,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        kluisz_project_id: str | None = None,
        kluisz_flow_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        max_traces: int = 500,
    ) -> dict[str, Any]:
        """Get aggregated usage statistics.
        
        Fetches traces and aggregates:
        - Total tokens (input, output, total)
        - Total cost
        - Number of traces
        - Active users (unique user_ids)
        
        Returns:
            Dictionary with aggregated statistics
        """
        traces = await self.get_all_traces(
            tenant_id=tenant_id,
            user_id=user_id,
            kluisz_project_id=kluisz_project_id,
            kluisz_flow_id=kluisz_flow_id,
            start_date=start_date,
            end_date=end_date,
            max_traces=max_traces,
        )
        
        total_tokens = 0
        input_tokens = 0
        output_tokens = 0
        total_cost = Decimal("0.00")
        active_users: set[str] = set()
        total_latency = 0.0
        
        for trace in traces:
            usage = trace.get("usage", {})
            total_tokens += usage.get("totalTokens", 0) or 0
            input_tokens += usage.get("inputTokens", 0) or 0
            output_tokens += usage.get("outputTokens", 0) or 0
            
            cost_value = usage.get("totalCost", 0) or 0
            try:
                total_cost += Decimal(str(cost_value))
            except Exception:
                pass
            
            if trace.get("user_id"):
                active_users.add(trace["user_id"])
            
            latency = trace.get("latency")
            if latency:
                total_latency += float(latency)
        
        return {
            "total_traces": len(traces),
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost_usd": float(total_cost),
            "active_users_count": len(active_users),
            "active_users": list(active_users),
            "average_latency": total_latency / len(traces) if traces else 0,
            "period_start": start_date.isoformat() if start_date else None,
            "period_end": end_date.isoformat() if end_date else None,
        }

    async def get_usage_by_model(
        self,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        max_traces: int = 500,
    ) -> dict[str, dict[str, Any]]:
        """Get usage breakdown by model."""
        traces = await self.get_all_traces(
            tenant_id=tenant_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            max_traces=max_traces,
        )
        
        by_model: dict[str, dict[str, Any]] = {}
        
        for trace in traces:
            metadata = trace.get("metadata", {})
            model = metadata.get("model", "unknown")
            usage = trace.get("usage", {})
            
            if model not in by_model:
                by_model[model] = {
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost_usd": 0.0,
                    "trace_count": 0,
                }
            
            by_model[model]["total_tokens"] += usage.get("totalTokens", 0) or 0
            by_model[model]["input_tokens"] += usage.get("inputTokens", 0) or 0
            by_model[model]["output_tokens"] += usage.get("outputTokens", 0) or 0
            by_model[model]["total_cost_usd"] += float(usage.get("totalCost", 0) or 0)
            by_model[model]["trace_count"] += 1
        
        return by_model

    async def get_usage_by_flow(
        self,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        max_traces: int = 500,
    ) -> dict[str, dict[str, Any]]:
        """Get usage breakdown by flow (kluisz_flow_id)."""
        traces = await self.get_all_traces(
            tenant_id=tenant_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            max_traces=max_traces,
        )
        
        by_flow: dict[str, dict[str, Any]] = {}
        
        for trace in traces:
            metadata = trace.get("metadata", {})
            flow_id = metadata.get("kluisz_flow_id") or trace.get("name", "unknown")
            usage = trace.get("usage", {})
            
            if flow_id not in by_flow:
                by_flow[flow_id] = {
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost_usd": 0.0,
                    "trace_count": 0,
                    "kluisz_project_id": metadata.get("kluisz_project_id"),
                }
            
            by_flow[flow_id]["total_tokens"] += usage.get("totalTokens", 0) or 0
            by_flow[flow_id]["input_tokens"] += usage.get("inputTokens", 0) or 0
            by_flow[flow_id]["output_tokens"] += usage.get("outputTokens", 0) or 0
            by_flow[flow_id]["total_cost_usd"] += float(usage.get("totalCost", 0) or 0)
            by_flow[flow_id]["trace_count"] += 1
        
        return by_flow

    async def get_daily_usage(
        self,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        max_traces: int = 500,
    ) -> list[dict[str, Any]]:
        """Get daily usage time series data."""
        traces = await self.get_all_traces(
            tenant_id=tenant_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            max_traces=max_traces,
        )
        
        by_day: dict[str, dict[str, Any]] = {}
        
        for trace in traces:
            timestamp = trace.get("timestamp")
            if not timestamp:
                continue
            
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except Exception:
                    continue
            
            date_key = timestamp.strftime("%Y-%m-%d")
            usage = trace.get("usage", {})
            
            if date_key not in by_day:
                by_day[date_key] = {
                    "date": date_key,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost_usd": 0.0,
                    "trace_count": 0,
                    "active_users": set(),
                }
            
            by_day[date_key]["total_tokens"] += usage.get("totalTokens", 0) or 0
            by_day[date_key]["input_tokens"] += usage.get("inputTokens", 0) or 0
            by_day[date_key]["output_tokens"] += usage.get("outputTokens", 0) or 0
            by_day[date_key]["total_cost_usd"] += float(usage.get("totalCost", 0) or 0)
            by_day[date_key]["trace_count"] += 1
            
            if trace.get("user_id"):
                by_day[date_key]["active_users"].add(trace["user_id"])
        
        # Convert to list and fix active_users
        result = []
        for day_data in sorted(by_day.values(), key=lambda x: x["date"]):
            day_data["active_users_count"] = len(day_data["active_users"])
            del day_data["active_users"]
            result.append(day_data)
        
        return result

    async def teardown(self) -> None:
        """Cleanup resources."""
        if self._client:
            try:
                self._client.shutdown()
            except Exception:
                pass
        self._client = None
        self._ready = False

