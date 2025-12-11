"""Seed default features into the registry."""

from datetime import datetime, timezone
from uuid import uuid4

from klx.log.logger import logger
from sqlmodel import select

# Default features to seed into the registry
# These are the BASELINE defaults - enabled by default for all license tiers
# Premium features are marked with is_premium=True
DEFAULT_FEATURES = [
    # ============================================
    # MODELS - LLM Provider Access
    # Basic AI models enabled by default
    # ============================================
    {
        "feature_key": "models.openai",
        "feature_name": "OpenAI Models",
        "category": "models",
        "subcategory": "openai",
        "default_value": {"enabled": True},  # ✅ Basic - enabled by default
        "description": "Access to OpenAI models (GPT-4, GPT-4o, GPT-3.5, etc.)",
    },
    {
        "feature_key": "models.anthropic",
        "feature_name": "Anthropic Models",
        "category": "models",
        "subcategory": "anthropic",
        "default_value": {"enabled": True},  # ✅ Basic - enabled by default
        "description": "Access to Claude models",
    },
    {
        "feature_key": "models.google",
        "feature_name": "Google AI Models",
        "category": "models",
        "subcategory": "google",
        "default_value": {"enabled": True},  # ✅ Basic - enabled by default
        "description": "Access to Gemini models",
    },
    {
        "feature_key": "models.mistral",
        "feature_name": "Mistral Models",
        "category": "models",
        "subcategory": "mistral",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Access to Mistral AI models",
    },
    {
        "feature_key": "models.ollama",
        "feature_name": "Ollama (Local)",
        "category": "models",
        "subcategory": "ollama",
        "default_value": {"enabled": True},  # ✅ Basic - local models
        "description": "Access to local Ollama models",
    },
    {
        "feature_key": "models.azure_openai",
        "feature_name": "Azure OpenAI",
        "category": "models",
        "subcategory": "azure",
        "default_value": {"enabled": False},  # Enterprise/Premium
        "is_premium": True,
        "description": "Access to Azure OpenAI service",
    },
    {
        "feature_key": "models.aws_bedrock",
        "feature_name": "AWS Bedrock",
        "category": "models",
        "subcategory": "aws",
        "default_value": {"enabled": False},  # Enterprise/Premium
        "is_premium": True,
        "description": "Access to AWS Bedrock models",
    },
    {
        "feature_key": "models.ibm_watsonx",
        "feature_name": "IBM watsonx.ai",
        "category": "models",
        "subcategory": "ibm",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Access to IBM watsonx.ai models",
    },
    {
        "feature_key": "models.groq",
        "feature_name": "Groq",
        "category": "models",
        "subcategory": "groq",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Access to Groq inference",
    },
    {
        "feature_key": "models.xai",
        "feature_name": "xAI (Grok)",
        "category": "models",
        "subcategory": "xai",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Access to xAI Grok models",
    },
    # ============================================
    # COMPONENTS - Flow Builder Blocks
    # All basic components enabled by default
    # ============================================
    {
        "feature_key": "components.models_and_agents",
        "feature_name": "Models & Agents",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": True},  # ✅ Core - AI Agent blocks
        "description": "Access to model and agent components (AI Agent block)",
    },
    {
        "feature_key": "components.helpers",
        "feature_name": "Helpers",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Access to helper components",
    },
    {
        "feature_key": "components.data_io",
        "feature_name": "Data I/O",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": True},  # ✅ Basic - File operations
        "description": "Access to data input/output components (file operations)",
    },
    {
        "feature_key": "components.logic",
        "feature_name": "Logic",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Access to logic components",
    },
    {
        "feature_key": "components.embeddings",
        "feature_name": "Embeddings",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Access to embedding components",
    },
    {
        "feature_key": "components.memories",
        "feature_name": "Memories",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Access to memory components",
    },
    {
        "feature_key": "components.tools",
        "feature_name": "Tools",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Access to tool components",
    },
    {
        "feature_key": "components.prototypes",
        "feature_name": "Prototypes (Beta)",
        "category": "components",
        "subcategory": "categories",
        "default_value": {"enabled": False},  # Disabled - Beta
        "description": "Access to beta/prototype components",
    },
    {
        "feature_key": "components.custom.enabled",
        "feature_name": "Create Custom Components",
        "category": "components",
        "subcategory": "custom",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Ability to create custom components",
    },
    {
        "feature_key": "components.custom.code_editing",
        "feature_name": "Edit Component Code",
        "category": "components",
        "subcategory": "custom",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Ability to edit component code",
    },
    {
        "feature_key": "components.custom.import_external",
        "feature_name": "Import External Components",
        "category": "components",
        "subcategory": "custom",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Ability to import components from external sources",
    },
    # ============================================
    # INTEGRATIONS - Third-party Services
    # ALL EXTERNAL INTEGRATIONS DISABLED BY DEFAULT
    # ============================================
    {
        "feature_key": "integrations.mcp",
        "feature_name": "MCP Server",
        "category": "integrations",
        "subcategory": "external",
        "default_value": {"enabled": False},  # ❌ OFF - External integration
        "is_premium": True,
        "description": "MCP Server integration",
    },
    # NOTE: All observability integrations (Langfuse, LangSmith, LangWatch) are 
    # mandatory/always-on for system logging - not feature-gated
    {
        "feature_key": "integrations.vector_stores.chroma",
        "feature_name": "Chroma",
        "category": "integrations",
        "subcategory": "vector_stores",
        "default_value": {"enabled": True},  # ✅ Local vector store OK
        "description": "Chroma vector store integration (local)",
    },
    {
        "feature_key": "integrations.vector_stores.pinecone",
        "feature_name": "Pinecone",
        "category": "integrations",
        "subcategory": "vector_stores",
        "default_value": {"enabled": False},  # ❌ OFF - External service
        "is_premium": True,
        "description": "Pinecone vector store integration",
    },
    {
        "feature_key": "integrations.vector_stores.qdrant",
        "feature_name": "Qdrant",
        "category": "integrations",
        "subcategory": "vector_stores",
        "default_value": {"enabled": False},  # ❌ OFF - External service
        "is_premium": True,
        "description": "Qdrant vector store integration",
    },
    {
        "feature_key": "integrations.vector_stores.weaviate",
        "feature_name": "Weaviate",
        "category": "integrations",
        "subcategory": "vector_stores",
        "default_value": {"enabled": False},  # ❌ OFF - External service
        "is_premium": True,
        "description": "Weaviate vector store integration",
    },
    # ============================================
    # INTEGRATION BUNDLES - External Third-Party Services
    # These control visibility of external integration component bundles in sidebar
    # Organized by category for easy admin configuration
    # ============================================
    
    # --- AI/ML Provider Bundles ---
    {
        "feature_key": "integrations.bundles.openai",
        "feature_name": "OpenAI Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": True},  # ✅ Basic - Common provider
        "description": "OpenAI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.anthropic",
        "feature_name": "Anthropic Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": True},  # ✅ Basic - Common provider
        "description": "Anthropic integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.google",
        "feature_name": "Google Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": True},  # ✅ Basic - Common provider
        "description": "Google AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.mistral",
        "feature_name": "Mistral Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Mistral AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.groq",
        "feature_name": "Groq Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Groq inference integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.cohere",
        "feature_name": "Cohere Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Cohere AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.huggingface",
        "feature_name": "HuggingFace Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "HuggingFace integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.ollama",
        "feature_name": "Ollama Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ OFF by default
        "is_premium": True,
        "description": "Ollama local models integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.baidu",
        "feature_name": "Baidu Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Baidu AI integration components bundle",
    },
    
    # --- Cloud Provider Bundles ---
    {
        "feature_key": "integrations.bundles.aws",
        "feature_name": "AWS Bundle",
        "category": "integrations",
        "subcategory": "bundles_cloud",
        "default_value": {"enabled": False},  # ❌ Premium - Enterprise
        "is_premium": True,
        "description": "AWS integration components bundle (Bedrock, SageMaker)",
    },
    {
        "feature_key": "integrations.bundles.azure",
        "feature_name": "Azure Bundle",
        "category": "integrations",
        "subcategory": "bundles_cloud",
        "default_value": {"enabled": False},  # ❌ Premium - Enterprise
        "is_premium": True,
        "description": "Azure integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.cloudflare",
        "feature_name": "Cloudflare Bundle",
        "category": "integrations",
        "subcategory": "bundles_cloud",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Cloudflare integration components bundle",
    },
    
    # --- Vector Store & Database Bundles ---
    {
        "feature_key": "integrations.bundles.chroma",
        "feature_name": "Chroma Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": True},  # ✅ Basic - Local vector store
        "description": "Chroma vector store integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.pinecone",
        "feature_name": "Pinecone Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Pinecone vector store integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.qdrant",
        "feature_name": "Qdrant Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Qdrant vector store integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.weaviate",
        "feature_name": "Weaviate Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Weaviate vector store integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.milvus",
        "feature_name": "Milvus Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Milvus vector store integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.cassandra",
        "feature_name": "Cassandra Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Cassandra database integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.datastax",
        "feature_name": "DataStax Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "DataStax/Astra DB integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.couchbase",
        "feature_name": "Couchbase Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Couchbase database integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.clickhouse",
        "feature_name": "ClickHouse Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "ClickHouse analytics database integration components bundle",
    },
    
    # --- Observability Bundles ---
    # NOTE: All observability bundles (Langfuse, LangSmith, LangWatch) are 
    # mandatory/always-on for system logging - not feature-gated
    {
        "feature_key": "integrations.bundles.comet",
        "feature_name": "Comet Bundle",
        "category": "integrations",
        "subcategory": "bundles_observability",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Comet ML observability integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.cleanlab",
        "feature_name": "Cleanlab Bundle",
        "category": "integrations",
        "subcategory": "bundles_observability",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Cleanlab data quality integration components bundle",
    },
    
    # --- External Service Bundles ---
    {
        "feature_key": "integrations.bundles.notion",
        "feature_name": "Notion Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Notion integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.confluence",
        "feature_name": "Confluence Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Confluence integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.apify",
        "feature_name": "Apify Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Apify web scraping integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.agentql",
        "feature_name": "AgentQL Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "AgentQL integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.assemblyai",
        "feature_name": "AssemblyAI Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "AssemblyAI speech-to-text integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.composio",
        "feature_name": "Composio Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Composio integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.arxiv",
        "feature_name": "arXiv Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": True},  # ✅ Basic - Research access
        "description": "arXiv research papers integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.bing",
        "feature_name": "Bing Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Bing search integration components bundle",
    },
    
    # --- Specialized Bundles ---
    {
        "feature_key": "integrations.bundles.altk",
        "feature_name": "ALTK Bundle",
        "category": "integrations",
        "subcategory": "bundles_specialized",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "ALTK integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.cuga",
        "feature_name": "CUGA Bundle",
        "category": "integrations",
        "subcategory": "bundles_specialized",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "CUGA integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.docling",
        "feature_name": "Docling Bundle",
        "category": "integrations",
        "subcategory": "bundles_specialized",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Docling document processing integration components bundle",
    },
    
    # --- Additional AI/ML Bundles ---
    {
        "feature_key": "integrations.bundles.aiml",
        "feature_name": "AI/ML API Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ OFF by default
        "is_premium": True,
        "description": "AI/ML API integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.deepseek",
        "feature_name": "DeepSeek Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "DeepSeek AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.xai",
        "feature_name": "xAI Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "xAI (Grok) integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.openrouter",
        "feature_name": "OpenRouter Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "OpenRouter model routing integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.perplexity",
        "feature_name": "Perplexity Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Perplexity AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.novita",
        "feature_name": "Novita Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Novita AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.nvidia",
        "feature_name": "NVIDIA Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium - Enterprise
        "is_premium": True,
        "description": "NVIDIA NIM integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.sambanova",
        "feature_name": "SambaNova Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "SambaNova AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.lmstudio",
        "feature_name": "LMStudio Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ OFF by default
        "is_premium": True,
        "description": "LMStudio local models integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.maritalk",
        "feature_name": "MariTalk Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "MariTalk AI integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.crewai",
        "feature_name": "CrewAI Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "CrewAI agent framework integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.ibm",
        "feature_name": "IBM Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium - Enterprise
        "is_premium": True,
        "description": "IBM watsonx.ai integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.vertexai",
        "feature_name": "Vertex AI Bundle",
        "category": "integrations",
        "subcategory": "bundles_ai",
        "default_value": {"enabled": False},  # ❌ Premium - Enterprise
        "is_premium": True,
        "description": "Google Vertex AI integration components bundle",
    },
    
    # --- Core Component Bundles ---
    {
        "feature_key": "integrations.bundles.languagemodels",
        "feature_name": "Language Models Bundle",
        "category": "integrations",
        "subcategory": "bundles_core",
        "default_value": {"enabled": True},  # ✅ Basic - Core functionality
        "description": "Language models integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.embeddings",
        "feature_name": "Embeddings Bundle",
        "category": "integrations",
        "subcategory": "bundles_core",
        "default_value": {"enabled": True},  # ✅ Basic - Core functionality
        "description": "Embeddings models integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.memories",
        "feature_name": "Memories Bundle",
        "category": "integrations",
        "subcategory": "bundles_core",
        "default_value": {"enabled": True},  # ✅ Basic - Core functionality
        "description": "Memory components integration bundle",
    },
    {
        "feature_key": "integrations.bundles.vectorstores",
        "feature_name": "Vector Stores Bundle",
        "category": "integrations",
        "subcategory": "bundles_core",
        "default_value": {"enabled": True},  # ✅ Basic - Core functionality
        "description": "Vector stores integration components bundle",
    },
    
    # --- Additional Database/Storage Bundles ---
    {
        "feature_key": "integrations.bundles.mongodb",
        "feature_name": "MongoDB Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "MongoDB database integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.redis",
        "feature_name": "Redis Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Redis cache/database integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.supabase",
        "feature_name": "Supabase Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Supabase database integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.upstash",
        "feature_name": "Upstash Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Upstash serverless database integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.elastic",
        "feature_name": "Elastic Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Elasticsearch integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.faiss",
        "feature_name": "FAISS Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": True},  # ✅ Basic - Local vector store
        "description": "FAISS local vector store integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.pgvector",
        "feature_name": "pgvector Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "PostgreSQL pgvector integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.vectara",
        "feature_name": "Vectara Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Vectara search platform integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.mem0",
        "feature_name": "Mem0 Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Mem0 memory layer integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.zep",
        "feature_name": "Zep Bundle",
        "category": "integrations",
        "subcategory": "bundles_data",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Zep memory store integration components bundle",
    },
    
    # --- Search & Web Services Bundles ---
    {
        "feature_key": "integrations.bundles.duckduckgo",
        "feature_name": "DuckDuckGo Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": True},  # ✅ Basic - Free search
        "description": "DuckDuckGo search integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.exa",
        "feature_name": "Exa Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Exa search integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.tavily",
        "feature_name": "Tavily Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Tavily AI search integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.searchapi",
        "feature_name": "SearchApi Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "SearchApi integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.serpapi",
        "feature_name": "SerpApi Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "SerpApi search integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.serper",
        "feature_name": "Serper Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Serper Google search integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.wikipedia",
        "feature_name": "Wikipedia Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": True},  # ✅ Basic - Free knowledge
        "description": "Wikipedia integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.wolframalpha",
        "feature_name": "WolframAlpha Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "WolframAlpha computational integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.youtube",
        "feature_name": "YouTube Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": True},  # ✅ Basic - Free content
        "description": "YouTube integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.yahoosearch",
        "feature_name": "Yahoo Finance Bundle",
        "category": "integrations",
        "subcategory": "bundles_search",
        "default_value": {"enabled": True},  # ✅ Basic - Free finance data
        "description": "Yahoo Finance integration components bundle",
    },
    
    # --- Document/Content Processing Bundles ---
    {
        "feature_key": "integrations.bundles.firecrawl",
        "feature_name": "Firecrawl Bundle",
        "category": "integrations",
        "subcategory": "bundles_content",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Firecrawl web crawling integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.scrapegraph",
        "feature_name": "ScrapeGraph Bundle",
        "category": "integrations",
        "subcategory": "bundles_content",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "ScrapeGraph AI web scraping integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.unstructured",
        "feature_name": "Unstructured Bundle",
        "category": "integrations",
        "subcategory": "bundles_content",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Unstructured document parsing integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.twelvelabs",
        "feature_name": "TwelveLabs Bundle",
        "category": "integrations",
        "subcategory": "bundles_content",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "TwelveLabs video understanding integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.vlmrun",
        "feature_name": "VLM Run Bundle",
        "category": "integrations",
        "subcategory": "bundles_content",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "VLM Run vision-language integration components bundle",
    },
    
    # --- Developer Tools Bundles ---
    {
        "feature_key": "integrations.bundles.git",
        "feature_name": "Git Bundle",
        "category": "integrations",
        "subcategory": "bundles_dev",
        "default_value": {"enabled": True},  # ✅ Basic - Developer tool
        "description": "Git repository integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.langchain",
        "feature_name": "LangChain Bundle",
        "category": "integrations",
        "subcategory": "bundles_dev",
        "default_value": {"enabled": True},  # ✅ Basic - Framework
        "description": "LangChain utilities integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.gmail",
        "feature_name": "Gmail Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Gmail integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.glean",
        "feature_name": "Glean Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium - Enterprise
        "is_premium": True,
        "description": "Glean enterprise search integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.needle",
        "feature_name": "Needle Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Needle integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.notdiamond",
        "feature_name": "Not Diamond Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Not Diamond AI routing integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.olivya",
        "feature_name": "Olivya Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Olivya integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.homeassistant",
        "feature_name": "Home Assistant Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Home Assistant smart home integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.icosacomputing",
        "feature_name": "Icosa Computing Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "Icosa Computing integration components bundle",
    },
    {
        "feature_key": "integrations.bundles.jigsawstack",
        "feature_name": "JigsawStack Bundle",
        "category": "integrations",
        "subcategory": "bundles_services",
        "default_value": {"enabled": False},  # ❌ Premium
        "is_premium": True,
        "description": "JigsawStack integration components bundle",
    },
    # ============================================
    # UI - User Interface Features
    # Basic UI enabled, API key mgmt OFF
    # ============================================
    {
        "feature_key": "ui.flow_builder.export_flow",
        "feature_name": "Export Flow",
        "category": "ui",
        "subcategory": "flow_builder",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Ability to export flows",
    },
    {
        "feature_key": "ui.flow_builder.import_flow",
        "feature_name": "Import Flow",
        "category": "ui",
        "subcategory": "flow_builder",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Ability to import flows",
    },
    {
        "feature_key": "ui.flow_builder.share_flow",
        "feature_name": "Share Flow",
        "category": "ui",
        "subcategory": "flow_builder",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Ability to share flows with team",
    },
    {
        "feature_key": "ui.flow_builder.version_control",
        "feature_name": "Version Control",
        "category": "ui",
        "subcategory": "flow_builder",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Flow version control",
    },
    {
        "feature_key": "ui.code_view.view_code",
        "feature_name": "View Code",
        "category": "ui",
        "subcategory": "code_view",
        "default_value": {"enabled": False},  # ❌ OFF by default
        "is_premium": True,
        "description": "Ability to view flow code",
    },
    {
        "feature_key": "ui.code_view.edit_code",
        "feature_name": "Edit Code",
        "category": "ui",
        "subcategory": "code_view",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Ability to edit flow code",
    },
    {
        "feature_key": "ui.code_view.python_api",
        "feature_name": "Python API",
        "category": "ui",
        "subcategory": "code_view",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Access to Python API view",
    },
    {
        "feature_key": "ui.debug.enabled",
        "feature_name": "Debug Mode",
        "category": "ui",
        "subcategory": "debug",
        "default_value": {"enabled": True},  # ✅ Basic - helpful for dev
        "description": "Enable debug mode",
    },
    {
        "feature_key": "ui.debug.step_execution",
        "feature_name": "Step Execution",
        "category": "ui",
        "subcategory": "debug",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Step-by-step flow execution",
    },
    {
        "feature_key": "ui.debug.logs_access",
        "feature_name": "Logs Access",
        "category": "ui",
        "subcategory": "debug",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Access to execution logs",
    },
    {
        "feature_key": "ui.advanced.global_variables",
        "feature_name": "Global Variables",
        "category": "ui",
        "subcategory": "advanced",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Global variables management",
    },
    {
        "feature_key": "ui.advanced.api_keys_management",
        "feature_name": "API Keys Management",
        "category": "ui",
        "subcategory": "advanced",
        "default_value": {"enabled": False},  # ❌ OFF - API key based access
        "is_premium": True,
        "description": "API keys management",
    },
    {
        "feature_key": "ui.advanced.mcp_server_config",
        "feature_name": "MCP Server Config",
        "category": "ui",
        "subcategory": "advanced",
        "default_value": {"enabled": False},  # ❌ OFF - MCP server access
        "is_premium": True,
        "description": "MCP server configuration",
    },
    {
        "feature_key": "ui.embed.enabled",
        "feature_name": "Embed Widget",
        "category": "ui",
        "subcategory": "sharing",
        "default_value": {"enabled": False},  # ❌ OFF - External embedding
        "is_premium": True,
        "description": "Embed flow as widget into external sites",
    },
    {
        "feature_key": "ui.chat.messages",
        "feature_name": "Messages",
        "category": "ui",
        "subcategory": "chat",
        "default_value": {"enabled": False},  # ❌ OFF by default
        "is_premium": True,
        "description": "Access to message history and management",
    },
    {
        "feature_key": "ui.playground.enabled",
        "feature_name": "Playground",
        "category": "ui",
        "subcategory": "testing",
        "default_value": {"enabled": True},  # ✅ Basic - Flow testing
        "description": "Access to flow playground for testing",
    },
    {
        "feature_key": "ui.templates.enabled",
        "feature_name": "Templates",
        "category": "ui",
        "subcategory": "templates",
        "default_value": {"enabled": True},  # ✅ Basic - Templates access
        "description": "Access to flow templates",
    },
    {
        "feature_key": "ui.store.enabled",
        "feature_name": "Component Store",
        "category": "ui",
        "subcategory": "store",
        "default_value": {"enabled": False},  # ❌ OFF - External store
        "is_premium": True,
        "description": "Access to component store",
    },
    # ============================================
    # API - API & External Access
    # Basic API enabled, advanced features OFF
    # ============================================
    {
        "feature_key": "api.public_endpoints",
        "feature_name": "Public API Endpoints",
        "category": "api",
        "subcategory": "access",
        "default_value": {"enabled": False},  # ❌ OFF by default
        "is_premium": True,
        "description": "Access to public API endpoints",
    },
    {
        "feature_key": "api.webhooks",
        "feature_name": "Webhooks",
        "category": "api",
        "subcategory": "access",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Webhook support",
    },
    {
        "feature_key": "api.streaming_responses",
        "feature_name": "Streaming Responses",
        "category": "api",
        "subcategory": "access",
        "default_value": {"enabled": True},  # ✅ Basic
        "description": "Streaming API responses",
    },
    {
        "feature_key": "api.batch_execution",
        "feature_name": "Batch Execution",
        "category": "api",
        "subcategory": "access",
        "default_value": {"enabled": False},  # Premium
        "is_premium": True,
        "description": "Batch flow execution",
    },
    # ============================================
    # LIMITS - Resource Limits
    # Reasonable defaults
    # ============================================
    {
        "feature_key": "limits.max_flows",
        "feature_name": "Max Flows",
        "category": "limits",
        "subcategory": "resources",
        "feature_type": "integer",
        "default_value": {"enabled": True, "value": 10},
        "description": "Maximum number of flows",
    },
    {
        "feature_key": "limits.max_api_calls_per_month",
        "feature_name": "Max API Calls/Month",
        "category": "limits",
        "subcategory": "resources",
        "feature_type": "integer",
        "default_value": {"enabled": True, "value": 1000},
        "description": "Maximum API calls per month",
    },
    {
        "feature_key": "limits.max_concurrent_executions",
        "feature_name": "Max Concurrent Executions",
        "category": "limits",
        "subcategory": "resources",
        "feature_type": "integer",
        "default_value": {"enabled": True, "value": 3},
        "description": "Maximum concurrent flow executions",
    },
    {
        "feature_key": "limits.max_file_upload_size_mb",
        "feature_name": "Max File Upload Size (MB)",
        "category": "limits",
        "subcategory": "resources",
        "feature_type": "integer",
        "default_value": {"enabled": True, "value": 10},
        "description": "Maximum file upload size in MB",
    },
]


async def seed_feature_registry(session) -> int:
    """
    Seed default features into the registry.

    Args:
        session: Database session

    Returns:
        Number of features seeded
    """
    from kluisz.services.database.models.feature.model import FeatureRegistry

    seeded_count = 0

    for idx, feature_data in enumerate(DEFAULT_FEATURES):
        # Check if exists
        stmt = select(FeatureRegistry).where(
            FeatureRegistry.feature_key == feature_data["feature_key"]
        )
        result = await session.exec(stmt)
        existing = result.first()

        if not existing:
            feature = FeatureRegistry(
                id=uuid4(),
                feature_key=feature_data["feature_key"],
                feature_name=feature_data["feature_name"],
                description=feature_data.get("description"),
                category=feature_data["category"],
                subcategory=feature_data.get("subcategory"),
                feature_type=feature_data.get("feature_type", "boolean"),
                default_value=feature_data["default_value"],
                is_premium=feature_data.get("is_premium", False),
                display_order=idx,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(feature)
            seeded_count += 1
            logger.debug(f"Seeded feature: {feature_data['feature_key']}")

    await session.commit()
    logger.info(f"Seeded {seeded_count} new features into registry")
    return seeded_count


async def seed_default_model_registry(session) -> int:
    """
    Seed default models into the model registry.

    Args:
        session: Database session

    Returns:
        Number of models seeded
    """
    from kluisz.services.database.models.feature.model import ModelRegistry

    default_models = [
        # OpenAI
        {"provider": "openai", "model_id": "gpt-4", "model_name": "GPT-4", "model_type": "chat", "feature_key": "models.openai", "supports_tools": True, "max_tokens": 8192},
        {"provider": "openai", "model_id": "gpt-4-turbo", "model_name": "GPT-4 Turbo", "model_type": "chat", "feature_key": "models.openai", "supports_tools": True, "supports_vision": True, "max_tokens": 128000},
        {"provider": "openai", "model_id": "gpt-4o", "model_name": "GPT-4o", "model_type": "chat", "feature_key": "models.openai", "supports_tools": True, "supports_vision": True, "max_tokens": 128000},
        {"provider": "openai", "model_id": "gpt-4o-mini", "model_name": "GPT-4o Mini", "model_type": "chat", "feature_key": "models.openai", "supports_tools": True, "supports_vision": True, "max_tokens": 128000},
        {"provider": "openai", "model_id": "gpt-3.5-turbo", "model_name": "GPT-3.5 Turbo", "model_type": "chat", "feature_key": "models.openai", "supports_tools": True, "max_tokens": 16385},
        # Anthropic
        {"provider": "anthropic", "model_id": "claude-3-opus-20240229", "model_name": "Claude 3 Opus", "model_type": "chat", "feature_key": "models.anthropic", "supports_tools": True, "supports_vision": True, "max_tokens": 200000},
        {"provider": "anthropic", "model_id": "claude-3-sonnet-20240229", "model_name": "Claude 3 Sonnet", "model_type": "chat", "feature_key": "models.anthropic", "supports_tools": True, "supports_vision": True, "max_tokens": 200000},
        {"provider": "anthropic", "model_id": "claude-3-5-sonnet-20241022", "model_name": "Claude 3.5 Sonnet", "model_type": "chat", "feature_key": "models.anthropic", "supports_tools": True, "supports_vision": True, "max_tokens": 200000},
        # Google
        {"provider": "google", "model_id": "gemini-pro", "model_name": "Gemini Pro", "model_type": "chat", "feature_key": "models.google", "supports_tools": True, "max_tokens": 32000},
        {"provider": "google", "model_id": "gemini-1.5-pro", "model_name": "Gemini 1.5 Pro", "model_type": "chat", "feature_key": "models.google", "supports_tools": True, "supports_vision": True, "max_tokens": 1000000},
    ]

    seeded_count = 0

    for model_data in default_models:
        stmt = select(ModelRegistry).where(
            ModelRegistry.provider == model_data["provider"],
            ModelRegistry.model_id == model_data["model_id"],
        )
        result = await session.exec(stmt)
        existing = result.first()

        if not existing:
            model = ModelRegistry(
                id=uuid4(),
                provider=model_data["provider"],
                model_id=model_data["model_id"],
                model_name=model_data["model_name"],
                model_type=model_data["model_type"],
                feature_key=model_data["feature_key"],
                supports_tools=model_data.get("supports_tools", False),
                supports_vision=model_data.get("supports_vision", False),
                max_tokens=model_data.get("max_tokens"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(model)
            seeded_count += 1

    await session.commit()
    logger.info(f"Seeded {seeded_count} new models into registry")
    return seeded_count
