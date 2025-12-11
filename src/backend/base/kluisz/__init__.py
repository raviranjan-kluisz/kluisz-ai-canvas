"""Kluisz backwards compatibility layer.

This module provides backwards compatibility by forwarding imports from
kluisz.* to klx.* to maintain compatibility with existing code that
references the old langflow module structure.
"""

import importlib
import importlib.util
import sys
from types import ModuleType
from typing import Any


class KluiszCompatibilityModule(ModuleType):
    """A module that forwards attribute access to the corresponding klx module."""

    def __init__(self, name: str, klx_module_name: str):
        super().__init__(name)
        self._klx_module_name = klx_module_name
        self._klx_module = None

    def _get_klx_module(self):
        """Lazily import and cache the klx module."""
        if self._klx_module is None:
            try:
                self._klx_module = importlib.import_module(self._klx_module_name)
            except ImportError as e:
                msg = f"Cannot import {self._klx_module_name} for backwards compatibility with {self.__name__}"
                raise ImportError(msg) from e
        return self._klx_module

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the klx module with caching."""
        klx_module = self._get_klx_module()
        try:
            attr = getattr(klx_module, name)
        except AttributeError as e:
            msg = f"module '{self.__name__}' has no attribute '{name}'"
            raise AttributeError(msg) from e
        else:
            # Cache the attribute in our __dict__ for faster subsequent access
            setattr(self, name, attr)
            return attr

    def __dir__(self):
        """Return directory of the klx module."""
        try:
            klx_module = self._get_klx_module()
            return dir(klx_module)
        except ImportError:
            return []


def _setup_compatibility_modules():
    """Set up comprehensive compatibility modules for kluisz.base imports."""
    # First, set up the base attribute on this module (kluisz)
    current_module = sys.modules[__name__]

    # Define all the modules we need to support
    module_mappings = {
        # Core base module
        "kluisz.base": "klx.base",
        # Inputs module - critical for class identity
        "kluisz.inputs": "klx.inputs",
        "kluisz.inputs.inputs": "klx.inputs.inputs",
        # Schema modules - also critical for class identity
        "kluisz.schema": "klx.schema",
        "kluisz.schema.data": "klx.schema.data",
        "kluisz.schema.serialize": "klx.schema.serialize",
        # Template modules
        "kluisz.template": "klx.template",
        "kluisz.template.field": "klx.template.field",
        "kluisz.template.field.base": "klx.template.field.base",
        # Components modules
        "kluisz.components": "klx.components",
        "kluisz.components.helpers": "klx.components.helpers",
        "kluisz.components.helpers.calculator_core": "klx.components.helpers.calculator_core",
        "kluisz.components.helpers.create_list": "klx.components.helpers.create_list",
        "kluisz.components.helpers.current_date": "klx.components.helpers.current_date",
        "kluisz.components.helpers.id_generator": "klx.components.helpers.id_generator",
        "kluisz.components.helpers.memory": "klx.components.helpers.memory",
        "kluisz.components.helpers.output_parser": "klx.components.helpers.output_parser",
        "kluisz.components.helpers.store_message": "klx.components.helpers.store_message",
        # Individual modules that exist in klx
        "kluisz.base.agents": "klx.base.agents",
        "kluisz.base.chains": "klx.base.chains",
        "kluisz.base.data": "klx.base.data",
        "kluisz.base.data.utils": "klx.base.data.utils",
        "kluisz.base.document_transformers": "klx.base.document_transformers",
        "kluisz.base.embeddings": "klx.base.embeddings",
        "kluisz.base.flow_processing": "klx.base.flow_processing",
        "kluisz.base.io": "klx.base.io",
        "kluisz.base.io.chat": "klx.base.io.chat",
        "kluisz.base.io.text": "klx.base.io.text",
        "kluisz.base.langchain_utilities": "klx.base.langchain_utilities",
        "kluisz.base.memory": "klx.base.memory",
        "kluisz.base.models": "klx.base.models",
        "kluisz.base.models.google_generative_ai_constants": "klx.base.models.google_generative_ai_constants",
        "kluisz.base.models.openai_constants": "klx.base.models.openai_constants",
        "kluisz.base.models.anthropic_constants": "klx.base.models.anthropic_constants",
        "kluisz.base.models.aiml_constants": "klx.base.models.aiml_constants",
        "kluisz.base.models.aws_constants": "klx.base.models.aws_constants",
        "kluisz.base.models.groq_constants": "klx.base.models.groq_constants",
        "kluisz.base.models.novita_constants": "klx.base.models.novita_constants",
        "kluisz.base.models.ollama_constants": "klx.base.models.ollama_constants",
        "kluisz.base.models.sambanova_constants": "klx.base.models.sambanova_constants",
        "kluisz.base.models.cometapi_constants": "klx.base.models.cometapi_constants",
        "kluisz.base.prompts": "klx.base.prompts",
        "kluisz.base.prompts.api_utils": "klx.base.prompts.api_utils",
        "kluisz.base.prompts.utils": "klx.base.prompts.utils",
        "kluisz.base.textsplitters": "klx.base.textsplitters",
        "kluisz.base.tools": "klx.base.tools",
        "kluisz.base.vectorstores": "klx.base.vectorstores",
    }

    # Create compatibility modules for each mapping
    for kluisz_name, klx_name in module_mappings.items():
        if kluisz_name not in sys.modules:
            # Check if the klx module exists
            try:
                spec = importlib.util.find_spec(klx_name)
                if spec is not None:
                    # Create compatibility module
                    compat_module = KluiszCompatibilityModule(kluisz_name, klx_name)
                    sys.modules[kluisz_name] = compat_module

                    # Set up the module hierarchy
                    parts = kluisz_name.split(".")
                    if len(parts) > 1:
                        parent_name = ".".join(parts[:-1])
                        parent_module = sys.modules.get(parent_name)
                        if parent_module is not None:
                            setattr(parent_module, parts[-1], compat_module)

                    # Special handling for top-level modules
                    if kluisz_name == "kluisz.base":
                        current_module.base = compat_module
                    elif kluisz_name == "kluisz.inputs":
                        current_module.inputs = compat_module
                    elif kluisz_name == "kluisz.schema":
                        current_module.schema = compat_module
                    elif kluisz_name == "kluisz.template":
                        current_module.template = compat_module
                    elif kluisz_name == "kluisz.components":
                        current_module.components = compat_module
            except (ImportError, ValueError):
                # Skip modules that don't exist in klx
                continue

    # Handle modules that exist only in kluisz (like knowledge_bases)
    # These need special handling because they're not in lfx yet
    kluisz_only_modules = {
        "kluisz.base.data.kb_utils": "kluisz.base.data.kb_utils",
        "kluisz.base.knowledge_bases": "kluisz.base.knowledge_bases",
        "kluisz.components.knowledge_bases": "kluisz.components.knowledge_bases",
    }

    for kluisz_name in kluisz_only_modules:
        if kluisz_name not in sys.modules:
            try:
                # Try to find the actual physical module file
                from pathlib import Path

                base_dir = Path(__file__).parent

                if kluisz_name == "kluisz.base.data.kb_utils":
                    kb_utils_file = base_dir / "base" / "data" / "kb_utils.py"
                    if kb_utils_file.exists():
                        spec = importlib.util.spec_from_file_location(kluisz_name, kb_utils_file)
                        if spec is not None and spec.loader is not None:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[kluisz_name] = module
                            spec.loader.exec_module(module)

                            # Also add to parent module
                            parent_module = sys.modules.get("kluisz.base.data")
                            if parent_module is not None:
                                parent_module.kb_utils = module

                elif kluisz_name == "kluisz.base.knowledge_bases":
                    kb_dir = base_dir / "base" / "knowledge_bases"
                    kb_init_file = kb_dir / "__init__.py"
                    if kb_init_file.exists():
                        spec = importlib.util.spec_from_file_location(kluisz_name, kb_init_file)
                        if spec is not None and spec.loader is not None:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[kluisz_name] = module
                            spec.loader.exec_module(module)

                            # Also add to parent module
                            parent_module = sys.modules.get("kluisz.base")
                            if parent_module is not None:
                                parent_module.knowledge_bases = module

                elif kluisz_name == "kluisz.components.knowledge_bases":
                    components_kb_dir = base_dir / "components" / "knowledge_bases"
                    components_kb_init_file = components_kb_dir / "__init__.py"
                    if components_kb_init_file.exists():
                        spec = importlib.util.spec_from_file_location(kluisz_name, components_kb_init_file)
                        if spec is not None and spec.loader is not None:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[kluisz_name] = module
                            spec.loader.exec_module(module)

                            # Also add to parent module
                            parent_module = sys.modules.get("kluisz.components")
                            if parent_module is not None:
                                parent_module.knowledge_bases = module
            except (ImportError, AttributeError):
                # If direct file loading fails, skip silently
                continue


# Set up all the compatibility modules
_setup_compatibility_modules()
