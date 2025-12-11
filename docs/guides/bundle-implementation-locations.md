# Bundle Implementation Locations

This document clarifies where bundles are actually implemented in Kluisz Kanvas.

## Quick Answer

**Bundles are implemented as folders in:**
```
src/klx/src/klx/components/
```

**NOT in:**
```
src/backend/base/kluisz/components/  ❌ (This is for custom Kluisz-specific components)
```

---

## Detailed Explanation

### 1. Component Implementation Location

All bundle components are located in the **KLX components package**:

```
src/klx/src/klx/components/
├── openai/              ← OpenAI bundle
│   ├── __init__.py
│   ├── openai.py
│   └── openai_chat_model.py
├── anthropic/           ← Anthropic bundle
│   ├── __init__.py
│   └── anthropic.py
├── chroma/              ← Chroma bundle
│   ├── __init__.py
│   └── chroma.py
├── mongodb/             ← MongoDB bundle
│   ├── __init__.py
│   └── mongodb.py
├── duckduckgo/          ← DuckDuckGo bundle
├── elastic/             ← Elastic bundle
├── firecrawl/           ← Firecrawl bundle
└── ... (100+ bundles)
```

### 2. How Bundles Work

1. **Folder Structure = Bundle Organization**
   - Each folder in `klx/components/` is a bundle
   - Folder name = Bundle identifier (e.g., `openai`, `chroma`)
   - Components in folder = Components in that bundle

2. **Component Loading**
   - API endpoint: `/api/v1/all`
   - Function: `import_langflow_components()` in `src/klx/src/klx/interface/components.py`
   - Scans `klx.components` package
   - Groups components by folder name (bundle name)
   - Returns: `{ "openai": {...}, "chroma": {...}, ... }`

3. **Frontend Mapping**
   - `SIDEBAR_BUNDLES` in `src/frontend/src/utils/styleUtils.ts` defines which bundles appear in sidebar
   - The `name` field must match the folder name in `klx/components/`
   - Example: `{ name: "openai", display_name: "OpenAI" }` → `klx/components/openai/`

4. **Feature Control**
   - Feature registry: `src/backend/base/kluisz/initial_setup/seed_features.py`
   - Feature maps: `src/frontend/src/constants/feature-maps.ts`
   - Controls visibility based on license tier

---

## File Structure Summary

| Location | Purpose | Example |
|----------|---------|---------|
| `src/klx/src/klx/components/<bundle>/` | **Component implementations** | `openai/openai.py` |
| `src/frontend/src/utils/styleUtils.ts` | Sidebar bundle list | `SIDEBAR_BUNDLES` |
| `src/frontend/src/constants/feature-maps.ts` | Feature key mappings | `BUNDLE_FEATURES` |
| `src/backend/base/kluisz/initial_setup/seed_features.py` | Feature registry seed | `integrations.bundles.openai` |
| `src/backend/base/kluisz/components/` | **Custom Kluisz components** (not bundles) | `knowledge_bases/`, `processing/` |

---

## Adding a New Bundle

### Step 1: Create Component Folder

```bash
mkdir -p src/klx/src/klx/components/myservice
```

### Step 2: Create Component Files

```python
# src/klx/src/klx/components/myservice/my_component.py
from klx.custom import Component
# ... component implementation
```

### Step 3: Register in __init__.py

```python
# src/klx/src/klx/components/myservice/__init__.py
# Use lazy loading pattern (see existing bundles)
```

### Step 4: Add to Frontend

1. Add to `SIDEBAR_BUNDLES` in `styleUtils.ts`:
   ```typescript
   { display_name: "MyService", name: "myservice", icon: "MyServiceIcon" }
   ```
   **Important**: `name: "myservice"` must match folder name!

2. Add to feature maps in `feature-maps.ts`:
   ```typescript
   MyService: "integrations.bundles.myservice"
   ```

3. Add to backend feature registry in `seed_features.py`:
   ```python
   {
       "feature_key": "integrations.bundles.myservice",
       "feature_name": "MyService Bundle",
       ...
   }
   ```

---

## Verification

To verify a bundle is implemented:

1. **Check folder exists:**
   ```bash
   ls src/klx/src/klx/components/<bundle_name>/
   ```

2. **Check API returns it:**
   ```bash
   curl http://localhost:3000/api/v1/all | jq 'keys | .[]' | grep <bundle_name>
   ```

3. **Check frontend mapping:**
   ```typescript
   // In styleUtils.ts
   SIDEBAR_BUNDLES.find(b => b.name === "<bundle_name>")
   ```

---

## Common Confusion

### ❌ Wrong Location
```
src/backend/base/kluisz/components/
```
This directory is for **Kluisz-specific custom components**, not Langflow/KLX bundles.

### ✅ Correct Location
```
src/klx/src/klx/components/
```
This is where **all bundle components** are implemented.

---

## Why This Architecture?

Kluisz Kanvas uses **KLX** (Kluisz Extension) as the component framework, which is based on Langflow. All standard components and bundles come from the KLX package, while Kluisz-specific extensions go in `kluisz/components/`.

This separation allows:
- **KLX components**: Reusable, standard components (OpenAI, Chroma, etc.)
- **Kluisz components**: Platform-specific features (knowledge bases, custom processing)

---

## Related Documentation

- [Adding Custom Bundles](./adding-custom-bundles.md) - Complete guide
- [Contributing Components](./contributing-components.md) - Component creation
- [Feature Control System](./feature-control-system.md) - License tier features

---

*Last updated: 2024*


