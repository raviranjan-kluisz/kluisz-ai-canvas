# Langfuse Tracer Enhancement

## Overview

This document describes how we enhance the Langfuse tracer to capture comprehensive observability data for the Kluisz Kanvas platform, including tenant context, project/flow identifiers, and usage metrics.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flow Execution                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Flow Run   │  │  Component   │  │   LLM Call   │       │
│  │   Execution  │→ │  Execution   │→ │   Execution   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ LangfuseTracer  │                        │
│                   │  - tenant_id    │                        │
│                   │  - user_id      │                        │
│                   │  - kluisz_project_id (folder_id) │       │
│                   │  - kluisz_flow_id (flow.id)      │       │
│                   └────────┬────────┘                        │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             │ HTTP/API
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    Langfuse Cloud                              │
│  - Traces with metadata                                        │
│  - Usage metrics (tokens, cost, latency)                     │
│  - Real-time and historical data                               │
└───────────────────────────────────────────────────────────────┘
```

## Enhanced Tracer Implementation

### Location

**File:** `src/backend/base/kluisz/services/tracing/langfuse.py`

### Key Enhancements

#### 1. Extended Constructor Parameters

The `LangFuseTracer` now accepts additional parameters for Kluisz-specific context:

```python
class LangFuseTracer(BaseTracer):
    def __init__(
        self,
        trace_name: str,
        trace_type: str,
        project_name: str,
        trace_id: UUID,
        user_id: str | None = None,
        session_id: str | None = None,
        tenant_id: str | None = None,  # NEW: Tenant context
        kluisz_project_id: str | None = None,  # NEW: folder_id
        kluisz_flow_id: str | None = None,  # NEW: flow.id
    ) -> None:
        # Store Kluisz-specific context
        self.tenant_id = tenant_id
        self.kluisz_project_id = kluisz_project_id  # folder_id from Flow model
        self.kluisz_flow_id = kluisz_flow_id  # flow.id from Flow model
```

#### 2. Enhanced Metadata Structure

All traces sent to Langfuse include comprehensive metadata:

```python
def setup_langfuse(self, config) -> bool:
    # Build metadata with Kluisz IDs
    metadata: dict[str, str] = {
        "trace_type": str(self.trace_type or "chain"),
    }
    
    # Always include these fields if available
    if self.tenant_id:
        metadata["tenant_id"] = str(self.tenant_id)
    if self.kluisz_project_id:
        metadata["kluisz_project_id"] = str(self.kluisz_project_id)  # folder_id
    if self.kluisz_flow_id:
        metadata["kluisz_flow_id"] = str(self.kluisz_flow_id)  # flow.id
    
    # Create trace with metadata
    self.trace = self._client.trace(
        id=str(self.trace_id),
        name=self.kluisz_flow_id or self.flow_id or self.trace_name,
        user_id=self.user_id,
        session_id=self.session_id,
        metadata=metadata,  # Includes tenant_id, kluisz_project_id, kluisz_flow_id
    )
```

### Metadata Structure

Every trace includes the following metadata structure:

```json
{
  "trace_type": "chain",
  "tenant_id": "uuid",
  "kluisz_project_id": "uuid (flow.folder_id)",
  "kluisz_flow_id": "uuid (flow.id)"
}
```

**Important Mappings:**
- `kluisz_project_id` = `flow.folder_id` (the Kluisz folder/project ID from URL: `/all/folder/{folder_id}`)
- `kluisz_flow_id` = `flow.id` (the Kluisz flow ID from URL: `/flow/{flow_id}/folder/{folder_id}`)
- `tenant_id` = Automatically fetched from user's tenant association

## Integration Points

### 1. Tracing Service Integration

**File:** `src/backend/base/kluisz/services/tracing/service.py`

The `TracingService` passes Kluisz context to the tracer:

```python
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
        self.tenant_id = tenant_id
        self.kluisz_project_id = kluisz_project_id
        self.kluisz_flow_id = kluisz_flow_id

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
    
    # Initialize Langfuse tracer with Kluisz context
    self._initialize_langfuse_tracer(trace_context)
```

### 2. Graph Initialization

**File:** `src/klx/src/klx/graph/graph/base.py`

The graph initialization passes folder_id and flow_id:

```python
async def initialize_run(self, folder_id: str | None = None) -> None:
    """Initialize a run for this graph.
    
    Args:
        folder_id: Kluisz folder_id (project ID) - should be passed from Flow model
    """
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

### 3. API Integration

**File:** `src/backend/base/kluisz/api/utils/core.py`

The API layer extracts folder_id from the Flow model:

```python
async def build_graph_from_db_no_cache(flow_id: UUID, session: AsyncSession, **kwargs):
    flow: Flow | None = await session.get(Flow, flow_id)
    if not flow or not flow.data:
        raise ValueError("Invalid flow ID")
    
    # Pass folder_id from flow
    return await build_graph_from_data(
        flow_id, 
        flow.data, 
        flow_name=flow.name,
        folder_id=flow.folder_id,  # NEW - pass folder_id
        **kwargs
    )
```

## Trace Data Captured

### 1. Trace-Level Data

- **Trace ID**: Unique identifier for the trace
- **Trace Name**: Uses `kluisz_flow_id` when available, falls back to flow name
- **User ID**: User executing the flow
- **Session ID**: Session identifier
- **Metadata**: Includes tenant_id, kluisz_project_id, kluisz_flow_id

### 2. Span-Level Data

Each component execution creates a span with:
- **Span ID**: Unique span identifier
- **Span Name**: Component name
- **Input/Output**: Component inputs and outputs
- **Latency**: Execution time
- **Status**: Success/failure

### 3. LLM Call Data

LLM calls automatically capture:
- **Model**: LLM model used
- **Tokens**: Input tokens, output tokens, total tokens
- **Cost**: Calculated cost in USD
- **Latency**: Response time
- **Prompt/Response**: Full prompt and response text

## Benefits

1. **Tenant Isolation**: All traces are tagged with tenant_id for proper multi-tenancy
2. **Project Context**: kluisz_project_id enables filtering by folder/project
3. **Flow Tracking**: kluisz_flow_id enables tracking specific flow usage
4. **User Attribution**: user_id enables user-level analytics
5. **Cost Tracking**: Automatic cost calculation from token usage
6. **Performance Monitoring**: Latency tracking for optimization

## Usage Example

```python
# When a flow runs:
# 1. Flow model provides folder_id and flow.id
# 2. User model provides tenant_id
# 3. Tracing service creates trace with all context

trace = LangFuseTracer(
    trace_name="My Flow - flow_123",
    trace_type="chain",
    project_name="langflow",
    trace_id=run_id,
    user_id="user_456",
    session_id="session_789",
    tenant_id="tenant_101",  # From user.tenant_id
    kluisz_project_id="folder_202",  # From flow.folder_id
    kluisz_flow_id="flow_123",  # From flow.id
)

# Trace sent to Langfuse with metadata:
# {
#   "tenant_id": "tenant_101",
#   "kluisz_project_id": "folder_202",
#   "kluisz_flow_id": "flow_123",
#   "trace_type": "chain"
# }
```

## Next Steps

After traces are sent to Langfuse with enhanced metadata:

1. **Analytics Service** processes traces to update usage statistics
2. **Pricing Engine** calculates costs based on token usage and tier pricing
3. **Usage Stats** are updated in `tenant_usage_stats` and `user_usage_stats` tables
4. **Dashboards** display real-time and historical usage data

See:
- [analytics-service.md](./analytics-service.md) - How analytics service processes traces
- [pricing-engine.md](./pricing-engine.md) - How costs are calculated

