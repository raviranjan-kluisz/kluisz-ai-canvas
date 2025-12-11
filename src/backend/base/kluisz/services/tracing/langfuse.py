from __future__ import annotations

import os
from collections import OrderedDict
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from klx.log.logger import logger
from typing_extensions import override

from kluisz.serialization.serialization import serialize
from kluisz.services.tracing.base import BaseTracer

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from langchain.callbacks.base import BaseCallbackHandler
    from klx.graph.vertex.base import Vertex

    from kluisz.services.tracing.schema import Log


class LangFuseTracer(BaseTracer):
    """Enhanced Langfuse tracer with Kluisz-specific metadata.
    
    Captures:
    - tenant_id: Tenant context for multi-tenancy
    - kluisz_project_id: folder_id from Flow model (project/folder ID)
    - kluisz_flow_id: flow.id from Flow model
    
    This metadata enables filtering and analytics by tenant, project, and flow.
    """
    
    flow_id: str

    def __init__(
        self,
        trace_name: str,
        trace_type: str,
        project_name: str,
        trace_id: UUID,
        user_id: str | None = None,
        session_id: str | None = None,
        tenant_id: str | None = None,  # Kluisz tenant context
        kluisz_project_id: str | None = None,  # folder_id from Flow model
        kluisz_flow_id: str | None = None,  # flow.id from Flow model
    ) -> None:
        self.project_name = project_name
        self.trace_name = trace_name
        self.trace_type = trace_type
        self.trace_id = trace_id
        self.user_id = user_id
        self.session_id = session_id
        self.flow_id = trace_name.split(" - ")[-1]
        
        # Kluisz-specific context
        self.tenant_id = tenant_id
        self.kluisz_project_id = kluisz_project_id  # folder_id
        self.kluisz_flow_id = kluisz_flow_id  # flow.id
        
        self.spans: dict = OrderedDict()  # spans that are not ended

        config = self._get_config()
        if not config:
            logger.warning("Langfuse not configured - missing environment variables. Set KLUISZ_LANGFUSE_SECRET_KEY, KLUISZ_LANGFUSE_PUBLIC_KEY, and KLUISZ_LANGFUSE_HOST (or BASE_URL)")
            self._ready = False
        else:
            self._ready: bool = self.setup_langfuse(config)

    @property
    def ready(self):
        return self._ready

    def setup_langfuse(self, config) -> bool:
        try:
            from langfuse import Langfuse

            self._client = Langfuse(**config)
            try:
                from langfuse.api.core.request_options import RequestOptions

                self._client.client.health.health(request_options=RequestOptions(timeout_in_seconds=1))
                logger.info(f"Langfuse tracer initialized successfully (host: {config.get('host', 'N/A')})")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Langfuse connection failed: {e}. Traces will not be sent to Langfuse.")
                return False
            
            # Build metadata with Kluisz IDs
            metadata: dict[str, str] = {
                "trace_type": str(self.trace_type or "chain"),
            }
            
            # Include Kluisz-specific metadata
            if self.tenant_id:
                metadata["tenant_id"] = str(self.tenant_id)
            if self.kluisz_project_id:
                metadata["kluisz_project_id"] = str(self.kluisz_project_id)  # folder_id
            if self.kluisz_flow_id:
                metadata["kluisz_flow_id"] = str(self.kluisz_flow_id)  # flow.id
            
            # Create trace with comprehensive metadata
            self.trace = self._client.trace(
                id=str(self.trace_id),
                name=self.kluisz_flow_id or self.flow_id,
                user_id=self.user_id,
                session_id=self.session_id,
                metadata=metadata,  # Includes tenant_id, kluisz_project_id, kluisz_flow_id
            )

        except ImportError:
            logger.warning("Langfuse SDK not installed. Install with: pip install langfuse")
            return False

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error setting up Langfuse tracer: {e}")
            return False

        return True

    @override
    def add_trace(
        self,
        trace_id: str,  # actualy component id
        trace_name: str,
        trace_type: str,
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        vertex: Vertex | None = None,
    ) -> None:
        start_time = datetime.now(tz=timezone.utc)
        if not self._ready:
            return

        metadata_: dict = {"from_langflow_component": True, "component_id": trace_id}
        metadata_ |= {"trace_type": trace_type} if trace_type else {}
        metadata_ |= metadata or {}

        name = trace_name.removesuffix(f" ({trace_id})")
        content_span = {
            "name": name,
            "input": inputs,
            "metadata": metadata_,
            "start_time": start_time,
        }

        # if two component is built concurrently, will use wrong last span. just flatten now, maybe fix in future.
        # if len(self.spans) > 0:
        #     last_span = next(reversed(self.spans))
        #     span = self.spans[last_span].span(**content_span)
        # else:
        span = self.trace.span(**serialize(content_span))

        self.spans[trace_id] = span

    @override
    def end_trace(
        self,
        trace_id: str,
        trace_name: str,
        outputs: dict[str, Any] | None = None,
        error: Exception | None = None,
        logs: Sequence[Log | dict] = (),
    ) -> None:
        end_time = datetime.now(tz=timezone.utc)
        if not self._ready:
            return

        span = self.spans.pop(trace_id, None)
        if span:
            output: dict = {}
            output |= outputs or {}
            output |= {"error": str(error)} if error else {}
            output |= {"logs": list(logs)} if logs else {}
            content = serialize({"output": output, "end_time": end_time})
            span.update(**content)

    @override
    def end(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        error: Exception | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self._ready:
            return
        content_update = {
            "input": inputs,
            "output": outputs,
            "metadata": metadata,
        }
        self.trace.update(**serialize(content_update))

    def get_langchain_callback(self) -> BaseCallbackHandler | None:
        if not self._ready:
            return None

        # get callback from parent span
        stateful_client = self.spans[next(reversed(self.spans))] if len(self.spans) > 0 else self.trace
        return stateful_client.get_langchain_handler()

    @staticmethod
    def _get_config() -> dict:
        """Get Langfuse configuration from environment variables.
        
        Supports both KLUISZ_LANGFUSE_* and LANGFUSE_* prefixes for backwards compatibility.
        Also supports both HOST and BASE_URL variants.
        """
        # Try Kluisz-prefixed env vars first, fall back to standard Langfuse ones
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
        return {}
