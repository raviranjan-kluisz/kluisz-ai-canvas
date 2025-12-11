"""
Feature Validation Service - Validates feature requirements for complex operations.

This service provides a centralized way to validate feature requirements
for operations that involve multiple features or complex logic.

Use this for:
- Flow execution validation
- Model usage validation
- Batch operations
- Complex multi-feature operations

@see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md - Pattern 5
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from klx.log.logger import logger

from kluisz.services.features.control_service import FeatureControlService


class OperationType(str, Enum):
    """Types of operations that can be validated."""
    
    # Flow operations
    EXECUTE_FLOW = "execute_flow"
    EXECUTE_FLOW_STREAMING = "execute_flow_streaming"
    EXECUTE_BATCH = "execute_batch"
    EXPORT_FLOW = "export_flow"
    IMPORT_FLOW = "import_flow"
    SHARE_FLOW = "share_flow"
    DUPLICATE_FLOW = "duplicate_flow"
    VERSION_CONTROL = "version_control"
    
    # Model operations
    USE_MODEL = "use_model"
    USE_EMBEDDING = "use_embedding"
    
    # Component operations
    CREATE_CUSTOM_COMPONENT = "create_custom_component"
    EDIT_COMPONENT_CODE = "edit_component_code"
    IMPORT_EXTERNAL_COMPONENT = "import_external_component"
    
    # Integration operations
    USE_MCP_SERVER = "use_mcp_server"
    ADD_MCP_SERVER = "add_mcp_server"
    # NOTE: All observability (Langfuse, LangSmith, LangWatch) is mandatory/always-on
    USE_VECTOR_STORE = "use_vector_store"
    
    # API operations
    CREATE_WEBHOOK = "create_webhook"
    CREATE_API_KEY = "create_api_key"
    USE_PUBLIC_API = "use_public_api"
    
    # Debug operations
    STEP_EXECUTION = "step_execution"
    VIEW_LOGS = "view_logs"


@dataclass
class ValidationResult:
    """Result of a feature validation check."""
    
    allowed: bool
    missing_features: List[str]
    message: str
    operation: str
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "missing_features": self.missing_features,
            "message": self.message,
            "operation": self.operation,
            "context": self.context,
        }


# Operation to feature requirements mapping
# Add new operations here - no code changes needed elsewhere
OPERATION_FEATURES: Dict[str, List[str]] = {
    # Flow operations
    OperationType.EXECUTE_FLOW: [],  # Basic execution always allowed
    OperationType.EXECUTE_FLOW_STREAMING: ["api.streaming_responses"],
    OperationType.EXECUTE_BATCH: ["api.batch_execution"],
    OperationType.EXPORT_FLOW: ["ui.flow_builder.export_flow"],
    OperationType.IMPORT_FLOW: ["ui.flow_builder.import_flow"],
    OperationType.SHARE_FLOW: ["ui.flow_builder.share_flow"],
    OperationType.DUPLICATE_FLOW: ["ui.flow_builder.duplicate_flow"],
    OperationType.VERSION_CONTROL: ["ui.flow_builder.version_control"],
    
    # Model operations (provider checked dynamically)
    OperationType.USE_MODEL: [],  # Checked per provider in context
    OperationType.USE_EMBEDDING: [],  # Checked per provider in context
    
    # Component operations
    OperationType.CREATE_CUSTOM_COMPONENT: ["components.custom.enabled"],
    OperationType.EDIT_COMPONENT_CODE: [
        "components.custom.code_editing",
        "ui.code_view.edit_code",
    ],
    OperationType.IMPORT_EXTERNAL_COMPONENT: ["components.custom.import_external"],
    
    # Integration operations
    OperationType.USE_MCP_SERVER: ["integrations.mcp"],
    OperationType.ADD_MCP_SERVER: [
        "integrations.mcp",
        "ui.advanced.mcp_server_config",
    ],
    # NOTE: All observability (Langfuse, LangSmith, LangWatch) is mandatory/always-on
    OperationType.USE_VECTOR_STORE: [],  # Checked per store in context
    
    # API operations
    OperationType.CREATE_WEBHOOK: ["api.webhooks"],
    OperationType.CREATE_API_KEY: ["ui.advanced.api_keys_management"],
    OperationType.USE_PUBLIC_API: ["api.public_endpoints"],
    
    # Debug operations
    OperationType.STEP_EXECUTION: ["ui.debug.step_execution"],
    OperationType.VIEW_LOGS: ["ui.debug.logs_access"],
}

# Provider to feature key mapping
PROVIDER_FEATURES: Dict[str, str] = {
    "openai": "models.openai",
    "anthropic": "models.anthropic",
    "google": "models.google",
    "mistral": "models.mistral",
    "ollama": "models.ollama",
    "azure_openai": "models.azure_openai",
    "azure": "models.azure_openai",
    "aws_bedrock": "models.aws_bedrock",
    "bedrock": "models.aws_bedrock",
    "ibm_watsonx": "models.ibm_watsonx",
    "groq": "models.groq",
    "xai": "models.xai",
    "cohere": "models.cohere",
    "huggingface": "models.huggingface",
}

# Vector store to feature key mapping
VECTOR_STORE_FEATURES: Dict[str, str] = {
    "chroma": "integrations.vector_stores.chroma",
    "pinecone": "integrations.vector_stores.pinecone",
    "qdrant": "integrations.vector_stores.qdrant",
    "weaviate": "integrations.vector_stores.weaviate",
    "milvus": "integrations.vector_stores.milvus",
}


class FeatureValidationService:
    """
    Validates feature requirements for complex operations.
    
    Usage:
        service = FeatureValidationService()
        result = await service.validate_operation(
            user_id="...",
            operation=OperationType.USE_MODEL,
            context={"provider": "openai"}
        )
        if not result.allowed:
            raise FeatureNotEnabled(result.missing_features)
    """

    def __init__(self):
        self.feature_service = FeatureControlService()

    async def validate_operation(
        self,
        user_id: str,
        operation: str | OperationType,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate if a user can perform an operation.
        
        Args:
            user_id: User UUID
            operation: Operation name from OPERATION_FEATURES or OperationType enum
            context: Additional context for dynamic feature checking
                     - provider: Model provider name (for USE_MODEL)
                     - vector_store: Vector store name (for USE_VECTOR_STORE)
        
        Returns:
            ValidationResult with allowed status and details
        """
        context = context or {}
        op_name = operation.value if isinstance(operation, OperationType) else operation

        # Get base required features
        required = list(OPERATION_FEATURES.get(op_name, []))

        # Handle dynamic feature requirements based on context
        required = self._add_context_features(op_name, context, required)

        if not required:
            return ValidationResult(
                allowed=True,
                missing_features=[],
                message="Operation allowed",
                operation=op_name,
                context=context,
            )

        # Check features (OR logic for base operation)
        missing = []
        has_any = False

        for feature_key in required:
            try:
                if await self.feature_service.is_feature_enabled(user_id, feature_key):
                    has_any = True
                    break
                else:
                    missing.append(feature_key)
            except Exception as e:
                await logger.awarning(f"Feature check error for {feature_key}: {e}")
                missing.append(feature_key)

        if has_any:
            return ValidationResult(
                allowed=True,
                missing_features=[],
                message="Operation allowed",
                operation=op_name,
                context=context,
            )

        return ValidationResult(
            allowed=False,
            missing_features=missing,
            message=f"Operation requires one of: {', '.join(missing)}",
            operation=op_name,
            context=context,
        )

    def _add_context_features(
        self,
        operation: str,
        context: Dict[str, Any],
        required: List[str],
    ) -> List[str]:
        """Add dynamic feature requirements based on context."""
        
        # Model provider check
        if operation in [OperationType.USE_MODEL, OperationType.USE_EMBEDDING, "use_model", "use_embedding"]:
            provider = context.get("provider", "").lower()
            if provider and provider in PROVIDER_FEATURES:
                required = [PROVIDER_FEATURES[provider]]

        # Vector store check
        if operation in [OperationType.USE_VECTOR_STORE, "use_vector_store"]:
            store = context.get("vector_store", "").lower()
            if store and store in VECTOR_STORE_FEATURES:
                required = [VECTOR_STORE_FEATURES[store]]

        return required

    async def validate_flow_execution(
        self,
        user_id: str,
        flow_data: Dict[str, Any],
        *,
        streaming: bool = False,
        batch: bool = False,
    ) -> ValidationResult:
        """
        Validate all features required to execute a flow.
        
        This checks:
        - Basic execution permissions
        - Streaming permissions (if enabled)
        - Batch permissions (if enabled)
        - Model provider permissions for all model nodes
        - Integration permissions for all integration nodes
        
        Args:
            user_id: User UUID
            flow_data: Flow data containing nodes
            streaming: Whether streaming is requested
            batch: Whether batch execution is requested
        
        Returns:
            ValidationResult with aggregated missing features
        """
        all_missing = []

        # Check execution type
        if streaming:
            result = await self.validate_operation(
                user_id, OperationType.EXECUTE_FLOW_STREAMING
            )
            if not result.allowed:
                all_missing.extend(result.missing_features)

        if batch:
            result = await self.validate_operation(
                user_id, OperationType.EXECUTE_BATCH
            )
            if not result.allowed:
                all_missing.extend(result.missing_features)

        # Check model nodes
        nodes = flow_data.get("nodes", [])
        for node in nodes:
            node_data = node.get("data", {})
            node_type = node_data.get("type", "")
            
            # Check for model components
            provider = self._detect_model_provider(node_data)
            if provider:
                result = await self.validate_operation(
                    user_id,
                    OperationType.USE_MODEL,
                    {"provider": provider},
                )
                if not result.allowed:
                    all_missing.extend(result.missing_features)

            # Check for MCP components
            if "mcp" in node_type.lower() or node_data.get("node", {}).get("template", {}).get("mcp_server"):
                result = await self.validate_operation(
                    user_id, OperationType.USE_MCP_SERVER
                )
                if not result.allowed:
                    all_missing.extend(result.missing_features)

        # Deduplicate
        all_missing = list(set(all_missing))

        if all_missing:
            return ValidationResult(
                allowed=False,
                missing_features=all_missing,
                message=f"Flow execution requires: {', '.join(all_missing)}",
                operation="execute_flow",
                context={"streaming": streaming, "batch": batch},
            )

        return ValidationResult(
            allowed=True,
            missing_features=[],
            message="Flow execution allowed",
            operation="execute_flow",
            context={"streaming": streaming, "batch": batch},
        )

    def _detect_model_provider(self, node_data: Dict[str, Any]) -> Optional[str]:
        """Detect the model provider from node data."""
        node_type = node_data.get("type", "").lower()
        display_name = node_data.get("node", {}).get("display_name", "").lower()
        
        # Check node type
        for provider, feature in PROVIDER_FEATURES.items():
            if provider in node_type or provider in display_name:
                return provider

        # Check template for provider field
        template = node_data.get("node", {}).get("template", {})
        model_name = template.get("model_name", {}).get("value", "")
        
        if "gpt" in model_name.lower() or "openai" in model_name.lower():
            return "openai"
        if "claude" in model_name.lower():
            return "anthropic"
        if "gemini" in model_name.lower():
            return "google"
        
        return None

    async def can_use_model(
        self,
        user_id: str,
        provider: str,
        model_id: Optional[str] = None,
    ) -> bool:
        """
        Quick check if user can use a specific model.
        
        Args:
            user_id: User UUID
            provider: Model provider name
            model_id: Optional specific model ID (for future per-model gating)
        
        Returns:
            True if the model is allowed
        """
        result = await self.validate_operation(
            user_id,
            OperationType.USE_MODEL,
            {"provider": provider, "model_id": model_id},
        )
        return result.allowed

    async def can_use_integration(
        self,
        user_id: str,
        integration: str,
    ) -> bool:
        """
        Quick check if user can use a specific integration.
        
        Args:
            user_id: User UUID
            integration: Integration name (mcp, pinecone, etc.)
        
        Returns:
            True if the integration is allowed
        """
        integration_lower = integration.lower()
        
        # All observability integrations are mandatory/always-on - always allowed
        if integration_lower in ("langfuse", "langsmith", "langwatch"):
            return True
        
        # Map to operation type
        operation_map = {
            "mcp": OperationType.USE_MCP_SERVER,
        }
        
        operation = operation_map.get(integration_lower)
        
        if operation:
            result = await self.validate_operation(user_id, operation)
            return result.allowed
        
        # Check vector stores
        if integration_lower in VECTOR_STORE_FEATURES:
            result = await self.validate_operation(
                user_id,
                OperationType.USE_VECTOR_STORE,
                {"vector_store": integration_lower},
            )
            return result.allowed
        
        # Unknown integration - allow by default
        return True


# Singleton instance
_validation_service: Optional[FeatureValidationService] = None


def get_validation_service() -> FeatureValidationService:
    """Get the singleton validation service instance."""
    global _validation_service
    if _validation_service is None:
        _validation_service = FeatureValidationService()
    return _validation_service


