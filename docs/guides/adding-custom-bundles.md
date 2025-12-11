# Adding Custom Integration Bundles to Kluisz Kanvas

This guide explains how to add new integration bundles to Kluisz Kanvas, making them available to users through the flow builder sidebar.

## Table of Contents

1. [Overview](#overview)
2. [Understanding Bundles](#understanding-bundles)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Code Locations](#code-locations)
5. [Testing Your Bundle](#testing-your-bundle)
6. [Best Practices](#best-practices)

---

## Overview

Integration bundles in Kluisz Kanvas are collections of related components that integrate with external services. For example:
- **OpenAI Bundle**: Contains ChatOpenAI, OpenAIEmbeddings, DALL-E, etc.
- **Chroma Bundle**: Contains ChromaDB vector store components
- **Langfuse Bundle**: Contains observability/tracing components

Bundles are:
- Displayed in the Flow Builder sidebar under "Bundles"
- Controlled by the **License Tier Feature System** (can be enabled/disabled per tenant)
- Organized by category (AI/ML, Databases, Search, etc.)

---

## Understanding Bundles

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Component Implementation (KLX)                  │
│  src/klx/src/klx/components/openai/                         │
│  ├── __init__.py                                            │
│  ├── openai.py (ChatOpenAI component)                       │
│  └── openai_chat_model.py (OpenAIModel component)          │
│                                                              │
│  Folder name = Bundle identifier = "openai"                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              API: /api/v1/all                                │
│  Returns: { "openai": { "ChatOpenAI": {...}, ... } }       │
│  Components grouped by folder name (bundle name)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Types Store                      │
│  data["openai"] = { "ChatOpenAI": {...}, ... }              │
│  Components organized by bundle name                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Sidebar Bundles List                      │
│  SIDEBAR_BUNDLES = [{ name: "openai", display_name: "OpenAI"}]│
│  name must match folder name in klx/components/              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Feature Registry (DB)                     │
│  feature_key: "integrations.bundles.openai"                 │
│  enabled: true/false (controlled per license tier)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Feature Maps                     │
│  BUNDLE_FEATURES["OpenAI"] = "integrations.bundles.openai"  │
│  BUNDLE_NAME_MAP["openai"] = "OpenAI"                       │
│  Used to filter bundles based on license tier               │
└─────────────────────────────────────────────────────────────┘
```

### Key Insight: Bundles = Folders

**Bundles are implemented as folders in `src/klx/src/klx/components/`:**

- Each folder = One bundle
- Folder name = Bundle identifier (must be lowercase, e.g., `openai`, `chroma`)
- Components in folder = Components in that bundle
- The API automatically groups components by folder name

**Example:**
```
src/klx/src/klx/components/
├── openai/          ← Bundle "openai"
│   ├── __init__.py
│   ├── openai.py
│   └── openai_chat_model.py
├── chroma/          ← Bundle "chroma"
│   ├── __init__.py
│   └── chroma.py
└── mongodb/         ← Bundle "mongodb"
    ├── __init__.py
    └── mongodb.py
```

When the API loads components, it returns:
```json
{
  "openai": {
    "ChatOpenAI": {...},
    "OpenAIModel": {...}
  },
  "chroma": {
    "ChromaVectorStore": {...}
  },
  "mongodb": {
    "MongoDB": {...}
  }
}
```

The frontend then uses `SIDEBAR_BUNDLES` to display these bundles in the sidebar, and `BUNDLE_FEATURES` to filter them based on license tiers.

### Feature Key Convention

All bundle feature keys follow this pattern:
```
integrations.bundles.<bundle_name>
```

Examples:
- `integrations.bundles.openai`
- `integrations.bundles.mongodb`
- `integrations.bundles.langfuse`

---

## Step-by-Step Guide

### Step 1: Add to Backend Feature Registry

Edit `src/backend/base/kluisz/initial_setup/seed_features.py`:

```python
DEFAULT_FEATURES = [
    # ... existing features ...
    
    # Add your new bundle
    {
        "feature_key": "integrations.bundles.myservice",
        "feature_name": "MyService Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",  # Choose appropriate subcategory
        "default_value": {"enabled": False},  # Start as premium/disabled
        "is_premium": True,
        "description": "MyService integration components bundle",
    },
]
```

**Subcategory Options:**
- `bundles_ai` - AI/ML providers (OpenAI, Anthropic, etc.)
- `bundles_cloud` - Cloud providers (AWS, Azure, GCP)
- `bundles_data` - Databases and vector stores
- `bundles_search` - Search engines and APIs
- `bundles_content` - Document/content processing
- `bundles_dev` - Developer tools
- `bundles_services` - External services
- `bundles_observability` - Monitoring/tracing
- `bundles_specialized` - Specialized/niche integrations
- `bundles_core` - Core platform components

### Step 2: Add to Frontend Feature Maps

Edit `src/frontend/src/constants/feature-maps.ts`:

**Add to BUNDLE_FEATURES:**
```typescript
export const BUNDLE_FEATURES: Record<string, string> = {
  // ... existing bundles ...
  
  // Add your new bundle (use PascalCase for key)
  MyService: "integrations.bundles.myservice",
};
```

**Add to BUNDLE_NAME_MAP:**
```typescript
const BUNDLE_NAME_MAP: Record<string, string> = {
  // ... existing mappings ...
  
  // Add mapping from sidebar name (lowercase) to BUNDLE_FEATURES key
  myservice: "MyService",
};
```

### Step 3: Add to Sidebar Bundles List

Edit `src/frontend/src/utils/styleUtils.ts`:

```typescript
export const SIDEBAR_BUNDLES = [
  // ... existing bundles (alphabetically sorted) ...
  
  { display_name: "MyService", name: "myservice", icon: "MyServiceIcon" },
];
```

**Critical**: The `name` field (`"myservice"`) **must match** the folder name in `src/klx/src/klx/components/myservice/`. This is how the frontend maps bundles to component folders.

**Note:** Keep the list alphabetically sorted for consistency.

### Step 4: Create Your Components

Components are what users actually drag onto the canvas. Create your component files in the **KLX components directory**:

```
src/klx/src/klx/components/
└── myservice/
    ├── __init__.py
    ├── chat_myservice.py
    ├── myservice_embeddings.py
    └── myservice_tools.py
```

**Important**: 
- The folder name (`myservice`) must match the `name` field in `SIDEBAR_BUNDLES` (lowercase)
- Components are automatically grouped by their folder name (bundle name)
- The API endpoint `/api/v1/all` returns components organized by folder name

Each component should:
1. Inherit from the appropriate base class (from `klx.custom` or `klx.base`)
2. Define inputs/outputs
3. Be registered in the folder's `__init__.py`

Example component:

```python
# src/klx/src/klx/components/myservice/chat_myservice.py

from klx.custom import Component
from klx.io import MessageTextInput, Output

class ChatMyService(Component):
    display_name = "MyService Chat"
    description = "Chat with MyService API"
    icon = "MyServiceIcon"
    name = "ChatMyService"
    
    # Note: The component automatically appears in the "myservice" bundle
    # because it's in the myservice/ folder. No explicit bundle assignment needed.
    
    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Input",
            info="The input message",
        ),
    ]
    
    outputs = [
        Output(display_name="Response", name="response", method="run"),
    ]
    
    def run(self, input_value: str) -> str:
        # Your implementation here
        return "Response from MyService"
```

Then register it in `__init__.py`:

```python
# src/klx/src/klx/components/myservice/__init__.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from klx.components._importing import import_mod

if TYPE_CHECKING:
    from .chat_myservice import ChatMyService

_dynamic_imports = {
    "ChatMyService": "chat_myservice",
}

__all__ = ["ChatMyService"]

def __getattr__(attr_name: str) -> Any:
    """Lazily import MyService components on attribute access."""
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)
    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    globals()[attr_name] = result
    return result

def __dir__() -> list[str]:
    return list(__all__)
```

### Step 5: Run Database Migration

After adding the feature to seed_features.py, the feature will be automatically seeded when the backend starts. Alternatively, create a migration:

```bash
cd src/backend/base
alembic revision --autogenerate -m "Add myservice bundle feature"
alembic upgrade head
```

### Step 6: Add Icon (Optional)

If you have a custom icon for your service:

1. Add SVG to `src/frontend/src/icons/`
2. Register in `src/frontend/src/utils/styleUtils.ts`:

```typescript
export const nodeIconToDisplayIconMap: Record<string, string> = {
  // ... existing icons ...
  MyService: "MyServiceIcon",
};
```

---

## Code Locations

| File | Purpose |
|------|---------|
| `src/backend/base/kluisz/initial_setup/seed_features.py` | Backend feature registry seed |
| `src/frontend/src/constants/feature-maps.ts` | Frontend feature key mappings |
| `src/frontend/src/utils/styleUtils.ts` | Sidebar bundle list + icons |
| `src/klx/src/klx/components/` | **Component implementations (bundles are folders here)** |
| `src/frontend/src/icons/` | Custom icons |

**Key Point**: Bundles are implemented as **folders** in `src/klx/src/klx/components/`. Each folder name becomes a bundle name that must match the `name` field in `SIDEBAR_BUNDLES`.

---

## Testing Your Bundle

### 1. Verify Feature is Seeded

Check the database:
```sql
SELECT * FROM feature_registry 
WHERE feature_key = 'integrations.bundles.myservice';
```

### 2. Enable for a License Tier

In the Super Admin UI:
1. Go to **Features** tab
2. Select a license tier (e.g., "Basic")
3. Find your bundle under "Integrations"
4. Toggle it ON
5. Save

### 3. Assign User to Tier

In the Tenant Admin UI:
1. Go to **License Management**
2. Assign a user to the tier with your bundle enabled

### 4. Verify in Flow Builder

1. Log in as the assigned user
2. Open Flow Builder
3. Check the "Bundles" section in the sidebar
4. Your bundle should appear if enabled

### 5. Test Component

1. Drag your component onto the canvas
2. Configure inputs
3. Run the flow
4. Verify output

---

## Best Practices

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Feature Key | `integrations.bundles.<lowercase>` | `integrations.bundles.openai` |
| BUNDLE_FEATURES Key | PascalCase | `OpenAI` |
| BUNDLE_NAME_MAP Key | lowercase (matches sidebar) | `openai` |
| Component Name | PascalCase | `ChatOpenAI` |
| Sidebar Name | lowercase | `openai` |
| Display Name | Human-readable | `"OpenAI"` |

### Default Values

- **Basic/Free tiers**: Set `default_value: {"enabled": True}` for commonly needed integrations
- **Premium features**: Set `default_value: {"enabled": False}` and `is_premium: True`
- **Local-only tools**: Enable by default (e.g., Ollama, FAISS)
- **External paid services**: Disable by default

### Documentation

Always include:
- Clear description in the feature definition
- Component docstrings
- Input/output descriptions
- Error handling messages

### Security

- Never hardcode API keys
- Use environment variables or the credentials system
- Validate all inputs
- Handle API errors gracefully

---

## Troubleshooting

### Bundle Not Appearing

1. **Check feature registry**: Ensure feature is seeded in database
2. **Check feature maps**: Verify BUNDLE_FEATURES and BUNDLE_NAME_MAP entries
3. **Check sidebar list**: Verify SIDEBAR_BUNDLES entry
4. **Check tier assignment**: Ensure user has a license tier with the feature enabled
5. **Clear cache**: Restart backend to clear feature cache

### Components Not Loading

1. **Check component metadata**: Ensure `name` matches expected format
2. **Check imports**: Verify all dependencies are installed
3. **Check logs**: Look for component loading errors in backend logs

### Feature Not Enforced

1. **Check cache TTL**: Feature cache expires after 5 minutes
2. **Verify user tier**: User must be assigned to a tier with the feature
3. **Check superadmin**: Superadmins bypass all feature checks

---

## Example: Complete Bundle Addition

Here's a complete example adding a hypothetical "Acme AI" integration:

### 1. seed_features.py
```python
{
    "feature_key": "integrations.bundles.acmeai",
    "feature_name": "Acme AI Bundle",
    "category": "integrations",
    "subcategory": "bundles_ai",
    "default_value": {"enabled": False},
    "is_premium": True,
    "description": "Acme AI models and tools integration",
},
```

### 2. feature-maps.ts
```typescript
// In BUNDLE_FEATURES
AcmeAI: "integrations.bundles.acmeai",

// In BUNDLE_NAME_MAP
acmeai: "AcmeAI",
```

### 3. styleUtils.ts
```typescript
{ display_name: "Acme AI", name: "acmeai", icon: "AcmeAI" },
```

### 4. Component (acme_chat.py)
```python
from kluisz.custom import Component
from kluisz.io import MessageTextInput, Output

class AcmeAIChat(Component):
    display_name = "Acme AI Chat"
    description = "Chat using Acme AI models"
    icon = "AcmeAI"
    name = "AcmeAIChat"
    
    inputs = [
        MessageTextInput(name="prompt", display_name="Prompt"),
    ]
    
    outputs = [
        Output(display_name="Response", name="response", method="run"),
    ]
    
    def run(self, prompt: str) -> str:
        # Implementation
        pass
```

---

## Next Steps

- [Contributing Components](./contributing-components.md) - Deep dive into component creation
- [Feature Control System](./feature-control-system.md) - Understanding the license tier system
- [Custom Components](./custom-components.md) - Creating user-defined components

---

*Last updated: 2024*


