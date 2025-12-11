# Contributing Components to Kluisz Kanvas

This guide explains how to create and contribute new components to Kluisz Kanvas. Components are the building blocks that users drag onto the canvas to build AI workflows.

## Table of Contents

1. [Overview](#overview)
2. [Component Types](#component-types)
3. [Creating a Component](#creating-a-component)
4. [Input/Output Types](#inputoutput-types)
5. [Component Metadata](#component-metadata)
6. [Advanced Features](#advanced-features)
7. [Testing Components](#testing-components)
8. [Submission Guidelines](#submission-guidelines)

---

## Overview

Components in Kluisz Kanvas are Python classes that:
- Define inputs and outputs
- Process data through a `run()` method
- Integrate with the visual flow builder

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Component Class                         │
├─────────────────────────────────────────────────────────────┤
│  Metadata:                                                   │
│  - display_name, description, icon                          │
│  - name (unique identifier)                                 │
├─────────────────────────────────────────────────────────────┤
│  Inputs:                                                    │
│  - MessageTextInput, IntInput, FileInput, etc.              │
├─────────────────────────────────────────────────────────────┤
│  Outputs:                                                   │
│  - Output (links to method)                                 │
├─────────────────────────────────────────────────────────────┤
│  Methods:                                                   │
│  - run(), build(), etc.                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Types

### 1. Standard Components

Regular components that process data synchronously.

```python
from kluisz.custom import Component
from kluisz.io import MessageTextInput, Output

class MyComponent(Component):
    display_name = "My Component"
    description = "Does something useful"
    
    inputs = [
        MessageTextInput(name="input_text", display_name="Input"),
    ]
    
    outputs = [
        Output(display_name="Result", name="result", method="run"),
    ]
    
    def run(self, input_text: str) -> str:
        return f"Processed: {input_text}"
```

### 2. Custom Components (User-Created)

Users with the "Custom Components" feature enabled can create their own components directly in the UI using Python code.

### 3. Integration Components

Components that connect to external services (APIs, databases, etc.).

```python
from kluisz.custom import Component
from kluisz.io import SecretStrInput, MessageTextInput, Output

class ExternalAPIComponent(Component):
    display_name = "External API"
    description = "Calls an external API"
    
    inputs = [
        SecretStrInput(name="api_key", display_name="API Key"),
        MessageTextInput(name="query", display_name="Query"),
    ]
    
    outputs = [
        Output(display_name="Response", name="response", method="run"),
    ]
    
    def run(self, api_key: str, query: str) -> str:
        # Make API call
        import requests
        response = requests.post(
            "https://api.example.com/query",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"query": query}
        )
        return response.json()["result"]
```

---

## Creating a Component

### Step 1: Choose the Right Location

Components are organized by bundle/category in the **KLX components directory**:

```
src/klx/src/klx/components/
├── openai/           # OpenAI bundle (ChatOpenAI, embeddings, etc.)
├── anthropic/        # Anthropic bundle
├── chroma/           # Chroma vector store bundle
├── mongodb/          # MongoDB bundle
├── models_and_agents/# Core models and agents
├── embeddings/       # Embedding models
├── vectorstores/     # Vector databases
├── tools/            # Agent tools
├── helpers/          # Utility components
├── data/             # Data processing
├── logic/            # Control flow
├── memories/         # Memory components
├── prototypes/       # Beta/experimental
└── <your_service>/   # Your new bundle folder
```

**Important**: 
- Each folder represents a **bundle**
- The folder name becomes the bundle identifier
- Components in a folder automatically belong to that bundle

### Step 2: Create the Component File

```python
# src/klx/src/klx/components/myservice/my_component.py

from klx.custom import Component
from kluisz.io import (
    MessageTextInput,
    IntInput,
    BoolInput,
    SecretStrInput,
    DropdownInput,
    FileInput,
    Output,
)

class MyServiceComponent(Component):
    """
    Component that integrates with MyService API.
    
    This component allows users to query MyService and get responses
    in their AI workflows.
    """
    
    # === Metadata ===
    display_name = "MyService Query"
    description = "Query MyService API for AI-powered responses"
    icon = "MyService"  # Icon name from icon registry
    name = "MyServiceQuery"  # Unique identifier (PascalCase, no spaces)
    
    # === Inputs ===
    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="Your MyService API key",
            required=True,
        ),
        MessageTextInput(
            name="query",
            display_name="Query",
            info="The query to send to MyService",
            required=True,
        ),
        DropdownInput(
            name="model",
            display_name="Model",
            info="Which model to use",
            options=["model-v1", "model-v2", "model-pro"],
            value="model-v1",
        ),
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            info="Maximum tokens in response",
            value=1024,
        ),
        BoolInput(
            name="stream",
            display_name="Stream Response",
            info="Whether to stream the response",
            value=False,
        ),
    ]
    
    # === Outputs ===
    outputs = [
        Output(
            display_name="Response",
            name="response",
            method="run",
        ),
    ]
    
    # === Main Method ===
    def run(
        self,
        api_key: str,
        query: str,
        model: str = "model-v1",
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str:
        """
        Execute the MyService query.
        
        Args:
            api_key: MyService API key
            query: The query to process
            model: Model to use
            max_tokens: Maximum response tokens
            stream: Whether to stream
            
        Returns:
            The API response text
        """
        import httpx
        
        response = httpx.post(
            "https://api.myservice.com/v1/query",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "model": model,
                "max_tokens": max_tokens,
            },
            timeout=30.0,
        )
        
        response.raise_for_status()
        return response.json()["result"]
```

### Step 3: Register the Component

Add to the bundle folder's `__init__.py`:

```python
# src/klx/src/klx/components/myservice/__init__.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from klx.components._importing import import_mod

if TYPE_CHECKING:
    from .my_component import MyServiceComponent

_dynamic_imports = {
    "MyServiceComponent": "my_component",
}

__all__ = ["MyServiceComponent"]

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

**Note**: KLX uses lazy loading with `__getattr__` for better performance. This pattern is required for all bundle `__init__.py` files.

---

## Input/Output Types

### Available Input Types

| Type | Description | Use Case |
|------|-------------|----------|
| `MessageTextInput` | Text input | Prompts, queries |
| `IntInput` | Integer input | Counts, limits |
| `FloatInput` | Float input | Temperature, thresholds |
| `BoolInput` | Boolean toggle | Feature flags |
| `SecretStrInput` | Hidden string | API keys, passwords |
| `DropdownInput` | Select from options | Model selection |
| `FileInput` | File upload | Documents, images |
| `MultiselectInput` | Multiple selections | Tags, categories |
| `DictInput` | Key-value pairs | Configuration |
| `NestedDictInput` | Nested objects | Complex config |
| `DataInput` | Accepts data from other nodes | Flow connections |

### Input Properties

```python
MessageTextInput(
    name="input_name",           # Internal name (snake_case)
    display_name="Display Name", # Shown in UI
    info="Help text",            # Tooltip
    required=True,               # Is required?
    value="default",             # Default value
    advanced=False,              # Show in advanced section?
    show=True,                   # Visible?
)
```

### Output Types

```python
Output(
    display_name="Result",    # Shown in UI
    name="result",            # Internal name
    method="run",             # Method that produces this output
)
```

### Multiple Outputs

```python
class MultiOutputComponent(Component):
    outputs = [
        Output(display_name="Success", name="success", method="run_success"),
        Output(display_name="Error", name="error", method="run_error"),
    ]
    
    def run_success(self, input_value: str) -> str:
        return "Success result"
    
    def run_error(self, input_value: str) -> str:
        return "Error result"
```

---

## Component Metadata

### Required Metadata

```python
class MyComponent(Component):
    display_name = "My Component"  # Shown in sidebar
    description = "What it does"   # Tooltip description
    name = "MyComponent"           # Unique ID (PascalCase)
```

### Optional Metadata

```python
class MyComponent(Component):
    icon = "Bot"                   # Icon name
    beta = True                    # Show beta badge
    legacy = True                  # Mark as legacy
    documentation = "https://..."  # Link to docs
    
    # For categorization
    CATEGORY = "helpers"           # Component category
```

### Icon Options

Common icons available:
- `Bot`, `Brain`, `BrainCircuit` - AI/ML
- `Database`, `Layers` - Data
- `Code`, `Terminal` - Development
- `Search`, `Globe` - Web/Search
- `FileText`, `File` - Documents
- `Hammer`, `Wrench` - Tools
- Brand icons: `OpenAI`, `Anthropic`, `Google`, etc.

---

## Advanced Features

### Async Components

For I/O-bound operations:

```python
class AsyncComponent(Component):
    async def run(self, input_value: str) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.example.com/{input_value}") as resp:
                return await resp.text()
```

### Streaming Responses

For real-time streaming:

```python
from typing import Generator

class StreamingComponent(Component):
    def run(self, prompt: str) -> Generator[str, None, None]:
        for chunk in self.call_streaming_api(prompt):
            yield chunk
```

### Dynamic Inputs

Inputs that change based on other inputs:

```python
class DynamicComponent(Component):
    inputs = [
        DropdownInput(
            name="provider",
            display_name="Provider",
            options=["openai", "anthropic"],
        ),
    ]
    
    def update_build_config(self, build_config, field_value, field_name):
        if field_name == "provider":
            if field_value == "openai":
                build_config["model"]["options"] = ["gpt-4", "gpt-3.5-turbo"]
            else:
                build_config["model"]["options"] = ["claude-3", "claude-2"]
        return build_config
```

### Error Handling

```python
class RobustComponent(Component):
    def run(self, input_value: str) -> str:
        try:
            result = self.process(input_value)
            return result
        except ValueError as e:
            self.status = f"Invalid input: {e}"
            raise
        except ConnectionError as e:
            self.status = "Connection failed"
            raise
        except Exception as e:
            self.status = f"Unexpected error: {e}"
            raise
```

### Using Credentials

```python
from kluisz.services.credentials import get_credential

class CredentialComponent(Component):
    def run(self, credential_name: str, query: str) -> str:
        # Get credential from secure storage
        api_key = get_credential(credential_name)
        return self.call_api(api_key, query)
```

---

## Testing Components

### Unit Tests

Create tests in `tests/unit/components/`:

```python
# tests/unit/components/test_myservice.py

import pytest
from kluisz.components.integrations.myservice import MyServiceComponent

class TestMyServiceComponent:
    def test_initialization(self):
        component = MyServiceComponent()
        assert component.display_name == "MyService Query"
        assert len(component.inputs) == 5
        assert len(component.outputs) == 1
    
    def test_run_success(self, mocker):
        component = MyServiceComponent()
        
        # Mock the API call
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"result": "test response"}
        mocker.patch("httpx.post", return_value=mock_response)
        
        result = component.run(
            api_key="test-key",
            query="test query",
        )
        
        assert result == "test response"
    
    def test_run_error(self, mocker):
        component = MyServiceComponent()
        
        # Mock API error
        mocker.patch("httpx.post", side_effect=Exception("API Error"))
        
        with pytest.raises(Exception):
            component.run(api_key="test-key", query="test")
```

### Integration Tests

```python
# tests/integration/test_myservice_integration.py

import pytest
from kluisz.components.integrations.myservice import MyServiceComponent

@pytest.mark.integration
class TestMyServiceIntegration:
    @pytest.fixture
    def api_key(self):
        import os
        return os.environ.get("MYSERVICE_API_KEY")
    
    def test_real_api_call(self, api_key):
        if not api_key:
            pytest.skip("API key not configured")
        
        component = MyServiceComponent()
        result = component.run(
            api_key=api_key,
            query="Hello world",
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
```

### Running Tests

```bash
# Run all component tests
pytest tests/unit/components/ -v

# Run specific test
pytest tests/unit/components/test_myservice.py -v

# Run integration tests (requires credentials)
pytest tests/integration/ -v -m integration
```

---

## Submission Guidelines

### Code Quality

1. **Type hints**: Use Python type hints for all parameters and returns
2. **Docstrings**: Include docstrings for classes and methods
3. **Error handling**: Handle errors gracefully with informative messages
4. **Logging**: Use the logging system for debug information

### Documentation

1. **Component description**: Clear, concise description
2. **Input descriptions**: Explain each input's purpose
3. **Examples**: Provide usage examples in docstrings

### Pull Request Checklist

- [ ] Component follows naming conventions
- [ ] All inputs have `info` descriptions
- [ ] Unit tests included
- [ ] Integration tests (if external service)
- [ ] No hardcoded credentials
- [ ] Error handling implemented
- [ ] Docstrings complete
- [ ] Bundle feature registered (if new bundle)

### Example PR Description

```markdown
## Summary
Adds MyService integration components to Kluisz Kanvas.

## Components Added
- `MyServiceQuery` - Query MyService API
- `MyServiceEmbeddings` - Generate embeddings

## Testing
- Added unit tests in `tests/unit/components/test_myservice.py`
- Tested manually against MyService API

## Feature Registry
- Added `integrations.bundles.myservice` feature
- Default: disabled (premium feature)

## Screenshots
[Include screenshots of component in sidebar and canvas]
```

---

## Common Patterns

### API Client Pattern

```python
class MyServiceBase(Component):
    """Base class for MyService components."""
    
    inputs = [
        SecretStrInput(name="api_key", display_name="API Key"),
    ]
    
    def get_client(self, api_key: str):
        """Get configured API client."""
        from myservice import Client
        return Client(api_key=api_key)


class MyServiceQuery(MyServiceBase):
    """Query component inheriting base configuration."""
    
    inputs = MyServiceBase.inputs + [
        MessageTextInput(name="query", display_name="Query"),
    ]
    
    def run(self, api_key: str, query: str) -> str:
        client = self.get_client(api_key)
        return client.query(query)
```

### Caching Pattern

```python
from functools import lru_cache

class CachedComponent(Component):
    @lru_cache(maxsize=100)
    def expensive_operation(self, input_value: str) -> str:
        # This result will be cached
        return self.call_api(input_value)
    
    def run(self, input_value: str) -> str:
        return self.expensive_operation(input_value)
```

### Retry Pattern

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class RetryComponent(Component):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def call_api(self, query: str) -> str:
        # Will retry up to 3 times with exponential backoff
        return self.api_client.query(query)
```

---

## Next Steps

- [Adding Custom Bundles](./adding-custom-bundles.md) - Create new integration bundles
- [Feature Control System](./feature-control-system.md) - License tier features
- [API Reference](./api-reference.md) - Complete API documentation

---

*Last updated: 2024*


