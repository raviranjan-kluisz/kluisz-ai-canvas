# Langfuse Observability Implementation Guide

## Step-by-Step Implementation

### Step 0: Super Admin Tenant Association (REQUIRED FIRST)

**IMPORTANT:** Before implementing Langfuse observability, ensure super admins are associated with tenants.

See [SUPER_ADMIN_TENANT_ASSOCIATION.md](../SUPER_ADMIN_TENANT_ASSOCIATION.md) for complete implementation.

**Quick Summary:**
1. Create default tenant helper function
2. Update `create_super_user` to associate with default tenant
3. Create migration for existing super admins
4. Update all super admin creation points

### Step 1: Enhance Langfuse Tracer

**File:** `src/backend/base/kluisz/services/tracing/langfuse.py`

```python
# Add tenant_id, kluisz_project_id, kluisz_flow_id to __init__
def __init__(
    self,
    trace_name: str,
    trace_type: str,
    project_name: str,
    trace_id: UUID,
    user_id: str | None = None,
    session_id: str | None = None,
    tenant_id: str | None = None,  # NEW
    kluisz_project_id: str | None = None,  # NEW - Kluisz folder_id (project ID)
    kluisz_flow_id: str | None = None,  # NEW - Kluisz flow.id
) -> None:
    self.project_name = project_name
    self.trace_name = trace_name
    self.trace_type = trace_type
    self.trace_id = trace_id
    self.user_id = user_id
    self.session_id = session_id
    # Store new fields
    self.tenant_id = tenant_id
    self.kluisz_project_id = kluisz_project_id  # folder_id from Flow model
    self.kluisz_flow_id = kluisz_flow_id  # flow.id from Flow model
    self.flow_id = trace_name.split(" - ")[-1]  # Keep existing for backward compatibility
    self.spans: dict = OrderedDict()

    config = self._get_config()
    self._ready: bool = self.setup_langfuse(config) if config else False

# Update setup_langfuse to include Kluisz metadata
def setup_langfuse(self, config) -> bool:
    try:
        from langfuse import Langfuse

        self._client = Langfuse(**config)
        try:
            from langfuse.api.core.request_options import RequestOptions

            self._client.client.health.health(request_options=RequestOptions(timeout_in_seconds=1))
        except Exception as e:  # noqa: BLE001
            logger.debug(f"can not connect to Langfuse: {e}")
            return False
        
        # Build metadata with Kluisz IDs
        metadata = {
            "trace_type": self.trace_type,
        }
        if self.tenant_id:
            metadata["tenant_id"] = self.tenant_id
        if self.kluisz_project_id:
            metadata["kluisz_project_id"] = self.kluisz_project_id  # folder_id
        if self.kluisz_flow_id:
            metadata["kluisz_flow_id"] = self.kluisz_flow_id  # flow.id
        
        self.trace = self._client.trace(
            id=str(self.trace_id),
            name=self.kluisz_flow_id or self.flow_id or self.trace_name,
            user_id=self.user_id,
            session_id=self.session_id,
            metadata=metadata,  # NEW: Includes Kluisz project_id and flow_id
        )

    except ImportError:
        logger.exception("Could not import langfuse. Please install it with `pip install langfuse`.")
        return False

    except Exception as e:  # noqa: BLE001
        logger.debug(f"Error setting up Langfuse tracer: {e}")
        return False

    return True
```

### Step 2: Update TraceContext and TracingService

**File:** `src/backend/base/kluisz/services/tracing/service.py`

```python
# Update TraceContext to include Kluisz IDs
class TraceContext:
    def __init__(
        self,
        run_id: UUID | None,
        run_name: str | None,
        project_name: str | None,
        user_id: str | None,
        session_id: str | None,
        tenant_id: str | None = None,  # NEW
        kluisz_project_id: str | None = None,  # NEW - folder_id
        kluisz_flow_id: str | None = None,  # NEW - flow.id
    ):
        self.run_id: UUID | None = run_id
        self.run_name: str | None = run_name
        self.project_name: str | None = project_name
        self.user_id: str | None = user_id
        self.session_id: str | None = session_id
        self.tenant_id: str | None = tenant_id  # NEW
        self.kluisz_project_id: str | None = kluisz_project_id  # NEW
        self.kluisz_flow_id: str | None = kluisz_flow_id  # NEW
        self.tracers: dict[str, BaseTracer] = {}
        self.all_inputs: dict[str, dict] = defaultdict(dict)
        self.all_outputs: dict[str, dict] = defaultdict(dict)
        self.traces_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.worker_task: asyncio.Task | None = None

# Update start_tracers to accept Kluisz IDs
async def start_tracers(
    self,
    run_id: UUID,
    run_name: str,
    user_id: str | None,
    session_id: str | None,
    project_name: str | None = None,
    tenant_id: str | None = None,  # NEW
    kluisz_project_id: str | None = None,  # NEW - folder_id
    kluisz_flow_id: str | None = None,  # NEW - flow.id
) -> None:
    """Start a trace for a graph run.
    
    Args:
        run_id: Unique run identifier
        run_name: Name of the run (e.g., "Flow Name - flow_id")
        user_id: User ID executing the flow
        session_id: Session ID for the run
        project_name: Langfuse project name (optional)
        tenant_id: Tenant ID (auto-fetched if not provided)
        kluisz_project_id: Kluisz folder_id (project ID) - REQUIRED
        kluisz_flow_id: Kluisz flow.id - REQUIRED
    """
    if self.deactivated:
        return
    try:
        project_name = project_name or os.getenv("LANGCHAIN_PROJECT", "Langflow")
        
        # Get tenant_id if not provided
        if user_id and not tenant_id:
            async with session_scope() as session:
                from kluisz.services.database.models.user.crud import get_user_by_id
                user = await get_user_by_id(session, UUID(user_id))
                if user and user.tenant_id:
                    tenant_id = str(user.tenant_id)
        
        # Create trace context with Kluisz IDs
        trace_context = TraceContext(
            run_id, run_name, project_name, user_id, session_id,
            tenant_id=tenant_id,
            kluisz_project_id=kluisz_project_id,
            kluisz_flow_id=kluisz_flow_id,
        )
        trace_context_var.set(trace_context)
        await self._start(trace_context)
        self._initialize_langsmith_tracer(trace_context)
        self._initialize_langwatch_tracer(trace_context)
        self._initialize_langfuse_tracer(trace_context)  # Pass Kluisz IDs
        self._initialize_arize_phoenix_tracer(trace_context)
        self._initialize_opik_tracer(trace_context)
        self._initialize_traceloop_tracer(trace_context)
    except Exception as e:  # noqa: BLE001
        await logger.adebug(f"Error initializing tracers: {e}")

# Update _initialize_langfuse_tracer to pass Kluisz IDs
def _initialize_langfuse_tracer(self, trace_context: TraceContext) -> None:
    langfuse_tracer = _get_langfuse_tracer()
    trace_context.tracers["langfuse"] = langfuse_tracer(
        trace_name=trace_context.run_name,
        trace_type="chain",
        project_name=trace_context.project_name,
        trace_id=trace_context.run_id,
        user_id=trace_context.user_id,
        session_id=trace_context.session_id,
        tenant_id=trace_context.tenant_id,
        kluisz_project_id=trace_context.kluisz_project_id,  # NEW
        kluisz_flow_id=trace_context.kluisz_flow_id,  # NEW
    )
```

### Step 3: Update Graph.initialize_run to Pass Kluisz IDs

**File:** `src/klx/src/klx/graph/graph/base.py`

```python
# Update initialize_run to accept and pass folder_id
async def initialize_run(self, folder_id: str | None = None) -> None:
    """Initialize a run for this graph.
    
    Args:
        folder_id: Kluisz folder_id (project ID) - should be passed from Flow model
    """
    if not self._run_id:
        self.set_run_id()
    if self.tracing_service:
        run_name = f"{self.flow_name} - {self.flow_id}"
        await self.tracing_service.start_tracers(
            run_id=uuid.UUID(self._run_id),
            run_name=run_name,
            user_id=self.user_id,
            session_id=self.session_id,
            kluisz_project_id=folder_id,  # NEW - pass folder_id
            kluisz_flow_id=self.flow_id,  # NEW - pass flow_id
        )
```

**File:** `src/backend/base/kluisz/api/utils/core.py`

```python
# Update build_graph_from_data to pass folder_id
async def build_graph_from_data(
    flow_id: uuid.UUID | str, 
    payload: dict, 
    folder_id: uuid.UUID | None = None,  # NEW
    **kwargs
):
    """Build and cache the graph."""
    # Get flow name
    if "flow_name" not in kwargs:
        flow_name = await _get_flow_name(flow_id if isinstance(flow_id, uuid.UUID) else uuid.UUID(flow_id))
    else:
        flow_name = kwargs["flow_name"]
    str_flow_id = str(flow_id)
    session_id = kwargs.get("session_id") or str_flow_id

    graph = Graph.from_payload(payload, str_flow_id, flow_name, kwargs.get("user_id"))
    for vertex_id in graph.has_session_id_vertices:
        vertex = graph.get_vertex(vertex_id)
        if vertex is None:
            msg = f"Vertex {vertex_id} not found"
            raise ValueError(msg)
        if not vertex.raw_params.get("session_id"):
            vertex.update_raw_params({"session_id": session_id}, overwrite=True)

    graph.session_id = session_id
    # Pass folder_id to initialize_run
    await graph.initialize_run(folder_id=str(folder_id) if folder_id else None)
    return graph

# Update build_graph_from_db_no_cache to pass folder_id
async def build_graph_from_db_no_cache(flow_id: uuid.UUID, session: AsyncSession, **kwargs):
    flow: Flow | None = await session.get(Flow, flow_id)
    if not flow or not flow.data:
        msg = "Invalid flow ID"
        raise ValueError(msg)
    kwargs["user_id"] = kwargs.get("user_id") or str(flow.user_id)
    # Pass folder_id from flow
    return await build_graph_from_data(
        flow_id, 
        flow.data, 
        flow_name=flow.name,
        folder_id=flow.folder_id,  # NEW - pass folder_id
        **kwargs
    )
```

**File:** `src/backend/base/kluisz/api/build.py`

```python
# Update create_graph to pass folder_id
async def create_graph(fresh_session, flow_id_str: str, flow_name: str | None) -> Graph:
    if inputs is not None and getattr(inputs, "session", None) is not None:
        effective_session_id = inputs.session
    else:
        effective_session_id = flow_id_str

    if not data:
        # Get flow to access folder_id
        flow = await fresh_session.get(Flow, flow_id)
        return await build_graph_from_db(
            flow_id=flow_id,
            session=fresh_session,
            chat_service=chat_service,
            user_id=str(current_user.id),
            session_id=effective_session_id,
            folder_id=flow.folder_id if flow else None,  # NEW
        )

    if not flow_name:
        result = await fresh_session.exec(select(Flow.name).where(Flow.id == flow_id))
        flow_name = result.first()
    
    # Get flow to access folder_id
    flow = await fresh_session.get(Flow, flow_id)
    return await build_graph_from_data(
        flow_id=flow_id_str,
        payload=data.model_dump(),
        user_id=str(current_user.id),
        flow_name=flow_name,
        session_id=effective_session_id,
        folder_id=flow.folder_id if flow else None,  # NEW
    )
```

### Step 4: Create Langfuse Client Service

**File:** `src/backend/base/kluisz/services/langfuse/__init__.py`
**File:** `src/backend/base/kluisz/services/langfuse/client_service.py`

```python
from langfuse import Langfuse
from langfuse.api.resources.commons.types.usage import Usage
from klx.services.base import Service
from klx.services.settings.service import SettingsService

class LangfuseClientService(Service):
    def __init__(self, settings_service: SettingsService):
        self.settings = settings_service.settings
        self._client = Langfuse(
            secret_key=self.settings.langfuse_secret_key,
            public_key=self.settings.langfuse_public_key,
            host=self.settings.langfuse_host
        )
    
    async def get_traces(
        self,
        project_id: str,  # Langfuse project_id
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        kluisz_project_id: str | None = None,  # NEW - filter by Kluisz folder_id
        kluisz_flow_id: str | None = None,  # NEW - filter by Kluisz flow.id
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 1000
    ) -> list[dict]:
        """Fetch traces from Langfuse API
        
        Args:
            project_id: Langfuse project ID (from tenant.langfuse_project_id)
            tenant_id: Filter by tenant_id in metadata
            user_id: Filter by user_id
            kluisz_project_id: Filter by kluisz_project_id in metadata (folder_id)
            kluisz_flow_id: Filter by kluisz_flow_id in metadata (flow.id)
        """
        filters = {}
        if tenant_id:
            filters["metadata.tenant_id"] = tenant_id
        if user_id:
            filters["user_id"] = user_id
        if kluisz_project_id:
            filters["metadata.kluisz_project_id"] = kluisz_project_id
        if kluisz_flow_id:
            filters["metadata.kluisz_flow_id"] = kluisz_flow_id
        
        # Use Langfuse SDK to fetch traces
        traces = []
        page = 1
        while len(traces) < limit:
            page_traces = self._client.fetch_traces(
                project_id=project_id,
                filters=filters,
                start_date=start_date,
                end_date=end_date,
                page=page,
                limit=min(100, limit - len(traces))
            )
            if not page_traces:
                break
            traces.extend(page_traces)
            page += 1
        
        return traces[:limit]
    
    async def get_usage_metrics(
        self,
        project_id: str,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        start_date: datetime,
        end_date: datetime
    ) -> UsageMetrics:
        """Get aggregated usage metrics"""
        # Implementation using Langfuse API
        pass
```

### Step 5: Create Usage Analytics Service

**File:** `src/backend/base/kluisz/services/usage/analytics_service.py`

```python
class UsageAnalyticsService(Service):
    def __init__(
        self,
        db_service: DatabaseService,
        langfuse_client: LangfuseClientService
    ):
        self.db_service = db_service
        self.langfuse_client = langfuse_client
    
    async def get_tenant_usage_stats(
        self,
        tenant_id: UUIDstr,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        group_by: str = "day"
    ) -> TenantUsageStats:
        """Get tenant-wide usage statistics"""
        # Query UsageRecord table
        # Aggregate by time period
        # Calculate top users, top flows
        # Return TenantUsageStats
        pass
```

### Step 6: Create API Endpoints

**File:** `src/backend/base/kluisz/api/v2/analytics.py`

```python
from fastapi import APIRouter, Depends, Query
from kluisz.services.auth.utils import get_current_user, get_current_tenant_admin
from kluisz.services.usage.analytics_service import UsageAnalyticsService

router = APIRouter(prefix="/api/v2/analytics", tags=["analytics"])

@router.get("/tenant/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: UUIDstr,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    group_by: str = Query("day"),
    current_user: User = Depends(get_current_tenant_admin),
    analytics_service: UsageAnalyticsService = Depends(get_analytics_service)
):
    """Get tenant-wide usage statistics"""
    stats = await analytics_service.get_tenant_usage_stats(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )
    return stats
```

### Step 7: Frontend Integration

**File:** `src/frontend/src/controllers/API/queries/analytics/use-usage-stats.ts`

```typescript
export function useUsageStats({ view, tenantId, userId }: UsageStatsParams) {
    return useQuery({
        queryKey: ["usage-stats", view, tenantId, userId],
        queryFn: () => {
            const endpoint = view === "platform" 
                ? "/api/v2/analytics/platform/stats"
                : view === "tenant"
                ? `/api/v2/analytics/tenant/${tenantId}/stats`
                : `/api/v2/analytics/user/${userId}/stats`;
            
            return api.get(endpoint).then(r => r.data);
        }
    });
}
```

---

## Testing

1. **Test Tracing**: 
   - Verify traces are sent with `kluisz_project_id` (folder_id) and `kluisz_flow_id` (flow.id) in metadata
   - Check that metadata includes: `tenant_id`, `kluisz_project_id`, `kluisz_flow_id`
   - Verify trace name uses `kluisz_flow_id` when available
2. **Test Metrics Retrieval**: 
   - Verify Langfuse API calls work with Kluisz ID filters
   - Test filtering by `kluisz_project_id` and `kluisz_flow_id`
3. **Test Analytics**: Verify statistics are calculated correctly using Kluisz IDs
4. **Test Dashboards**: Verify frontend displays data correctly with Kluisz project/flow context

## Important Notes

1. **Kluisz IDs vs Langfuse IDs**:
   - `kluisz_project_id` = `flow.folder_id` (the Kluisz folder/project ID)
   - `kluisz_flow_id` = `flow.id` (the Kluisz flow ID)
   - `langfuse_project_id` = `tenant.langfuse_project_id` (the Langfuse project ID for the tenant)
   
2. **Metadata Structure in Langfuse**:
   ```json
   {
     "tenant_id": "uuid",
     "kluisz_project_id": "uuid (folder_id)",
     "kluisz_flow_id": "uuid (flow.id)",
     "trace_type": "chain"
   }
   ```

3. **URL Mapping**:
   - Project URL: `/all/folder/{folder_id}` → `kluisz_project_id` = `folder_id`
   - Flow URL: `/flow/{flow_id}/folder/{folder_id}` → `kluisz_flow_id` = `flow_id`, `kluisz_project_id` = `folder_id`

