/**
 * Feature Maps - Central configuration for feature-to-resource mappings.
 * 
 * This file is the SINGLE SOURCE OF TRUTH for all UI-level feature gating.
 * To add feature protection to a new UI element, add it to the appropriate map.
 * No component code changes needed.
 * 
 * @see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md
 */

// =============================================================================
// MODEL PROVIDER FEATURES
// =============================================================================

/**
 * Maps model providers to their feature keys.
 * Used by useFilteredModels hook to filter model dropdowns.
 */
export const PROVIDER_FEATURE_MAP: Record<string, string> = {
  openai: "models.openai",
  anthropic: "models.anthropic",
  google: "models.google",
  mistral: "models.mistral",
  ollama: "models.ollama",
  azure_openai: "models.azure_openai",
  azure: "models.azure_openai",
  aws_bedrock: "models.aws_bedrock",
  bedrock: "models.aws_bedrock",
  ibm_watsonx: "models.ibm_watsonx",
  watsonx: "models.ibm_watsonx",
  groq: "models.groq",
  xai: "models.xai",
  cohere: "models.cohere",
  huggingface: "models.huggingface",
  replicate: "models.replicate",
  together: "models.together",
  fireworks: "models.fireworks",
  deepseek: "models.deepseek",
  perplexity: "models.perplexity",
};

// =============================================================================
// COMPONENT CATEGORY FEATURES
// =============================================================================

/**
 * Maps component categories to their feature keys.
 * Used to filter entire categories in the flow sidebar.
 */
export const COMPONENT_CATEGORY_FEATURES: Record<string, string> = {
  // Core categories
  models_and_agents: "components.models_and_agents",
  helpers: "components.helpers",
  data_io: "components.data_io",
  logic: "components.logic",
  embeddings: "components.embeddings",
  memories: "components.memories",
  tools: "components.tools",
  prototypes: "components.prototypes",
  
  // Special categories
  MCP: "integrations.mcp",
  custom_component: "components.custom.enabled",
  
  // Vector store categories
  vectorstores: "components.vectorstores",
  
  // Deprecated/legacy (still need mapping for backwards compat)
  agents: "components.models_and_agents",
  models: "components.models_and_agents",
};

// =============================================================================
// SETTINGS SIDEBAR FEATURES
// =============================================================================

/**
 * Maps settings sidebar items to their required features.
 * Array = OR logic (any feature enables the item).
 */
export const SETTINGS_SIDEBAR_FEATURES: Record<string, string[]> = {
  "mcp-servers": ["integrations.mcp", "ui.advanced.mcp_server_config"],
  "api-keys": ["ui.advanced.api_keys_management"],
  "global-variables": ["ui.advanced.global_variables"],
  "store": ["ui.store.enabled"],
  // NOTE: All observability (langfuse, langsmith, langwatch) is mandatory/always-on
  "messages": ["ui.chat.messages"],
};

// =============================================================================
// FLOW TOOLBAR FEATURES
// =============================================================================

/**
 * Maps flow toolbar actions to their required features.
 */
export const FLOW_TOOLBAR_FEATURES: Record<string, string[]> = {
  export: ["ui.flow_builder.export_flow"],
  import: ["ui.flow_builder.import_flow"],
  share: ["ui.flow_builder.share_flow"],
  duplicate: ["ui.flow_builder.duplicate_flow"],
  "version-history": ["ui.flow_builder.version_control"],
  "api-access": ["api.public_endpoints"],
  "python-api": ["ui.code_view.python_api"],
  webhook: ["api.webhooks"],
  "embed-widget": ["ui.embed.enabled"],
};

// =============================================================================
// NODE TOOLBAR FEATURES
// =============================================================================

/**
 * Maps node toolbar actions to their required features.
 */
export const NODE_TOOLBAR_FEATURES: Record<string, string[]> = {
  code: ["components.custom.code_editing", "ui.code_view.edit_code"],
  "save-component": ["components.custom.enabled"],
  share: ["ui.flow_builder.share_flow"],
  download: ["ui.flow_builder.export_flow"],
};

// =============================================================================
// DEBUG & ADVANCED FEATURES
// =============================================================================

/**
 * Maps debug/advanced features to their feature keys.
 */
export const DEBUG_FEATURES: Record<string, string> = {
  "step-execution": "ui.debug.step_execution",
  "logs-access": "ui.debug.logs_access",
  "debug-mode": "ui.debug.enabled",
  "view-code": "ui.code_view.view_code",
  "edit-code": "ui.code_view.edit_code",
};

// =============================================================================
// INTEGRATION FEATURES
// =============================================================================

/**
 * Maps integrations to their feature keys.
 */
export const INTEGRATION_FEATURES: Record<string, string> = {
  mcp: "integrations.mcp",
  // NOTE: All observability (langfuse, langsmith, langwatch) is mandatory/always-on
  
  // Vector stores
  chroma: "integrations.vector_stores.chroma",
  pinecone: "integrations.vector_stores.pinecone",
  qdrant: "integrations.vector_stores.qdrant",
  weaviate: "integrations.vector_stores.weaviate",
  milvus: "integrations.vector_stores.milvus",
  
  // Databases
  postgres: "integrations.databases.postgres",
  mongodb: "integrations.databases.mongodb",
  airtable: "integrations.databases.airtable",
  notion: "integrations.databases.notion",
};

// =============================================================================
// COMPONENT TYPE TO FEATURE MAPPING
// =============================================================================

/**
 * Maps specific component types to their feature keys.
 * Used for fine-grained component filtering.
 */
export const COMPONENT_TYPE_FEATURES: Record<string, string> = {
  // OpenAI components
  ChatOpenAI: "models.openai",
  OpenAIEmbeddings: "models.openai",
  OpenAIModel: "models.openai",
  
  // Anthropic components
  ChatAnthropic: "models.anthropic",
  AnthropicModel: "models.anthropic",
  
  // Google components
  ChatGoogleGenerativeAI: "models.google",
  GoogleGenerativeAIEmbeddings: "models.google",
  VertexAI: "models.google",
  
  // Azure OpenAI
  AzureChatOpenAI: "models.azure_openai",
  AzureOpenAIEmbeddings: "models.azure_openai",
  
  // AWS Bedrock
  BedrockChat: "models.aws_bedrock",
  BedrockEmbeddings: "models.aws_bedrock",
  
  // Ollama
  ChatOllama: "models.ollama",
  OllamaEmbeddings: "models.ollama",
  
  // Mistral
  ChatMistralAI: "models.mistral",
  MistralAIEmbeddings: "models.mistral",
  
  // Groq
  ChatGroq: "models.groq",
  
  // Custom components
  CustomComponent: "components.custom.enabled",
  
  // MCP
  MCPTools: "integrations.mcp",
  MCPServer: "integrations.mcp",
  
  // Vector stores
  Chroma: "integrations.vector_stores.chroma",
  Pinecone: "integrations.vector_stores.pinecone",
  Qdrant: "integrations.vector_stores.qdrant",
  Weaviate: "integrations.vector_stores.weaviate",
  Milvus: "integrations.vector_stores.milvus",
};

// =============================================================================
// SIDEBAR SEGMENT FEATURES
// =============================================================================

/**
 * Maps sidebar segments/sections to their feature keys.
 * Used by the segmented sidebar navigation.
 */
export const SIDEBAR_SEGMENT_FEATURES: Record<string, string[]> = {
  components: [], // Always visible - core functionality
  bundles: [], // Always visible - but individual bundles can be gated
  mcp: ["integrations.mcp"],
  search: [], // Always visible
  add_note: [], // Always visible - core functionality
};

// =============================================================================
// NAVIGATION ITEM FEATURES
// =============================================================================

/**
 * Maps main navigation items to their feature keys.
 * Used by the main app sidebar navigation.
 */
export const NAVIGATION_FEATURES: Record<string, string[]> = {
  messages: ["ui.chat.messages"],
  playground: ["ui.playground.enabled"],
  flows: [], // Always visible - core functionality
  templates: ["ui.templates.enabled"],
  store: ["ui.store.enabled"],
};

// =============================================================================
// EXTERNAL INTEGRATION BUNDLE FEATURES
// =============================================================================

/**
 * Maps external integration bundles (sidebar bundles) to their feature keys.
 * These are third-party integrations that can be controlled per tenant.
 */
export const BUNDLE_FEATURES: Record<string, string> = {
  // ===========================================
  // AI/ML Provider Bundles
  // ===========================================
  OpenAI: "integrations.bundles.openai",
  Anthropic: "integrations.bundles.anthropic",
  Google: "integrations.bundles.google",
  Mistral: "integrations.bundles.mistral",
  Groq: "integrations.bundles.groq",
  Azure: "integrations.bundles.azure",
  Cohere: "integrations.bundles.cohere",
  HuggingFace: "integrations.bundles.huggingface",
  Ollama: "integrations.bundles.ollama",
  AWS: "integrations.bundles.aws",
  Amazon: "integrations.bundles.aws",
  DeepSeek: "integrations.bundles.deepseek",
  xAI: "integrations.bundles.xai",
  OpenRouter: "integrations.bundles.openrouter",
  Perplexity: "integrations.bundles.perplexity",
  Novita: "integrations.bundles.novita",
  NVIDIA: "integrations.bundles.nvidia",
  SambaNova: "integrations.bundles.sambanova",
  LMStudio: "integrations.bundles.lmstudio",
  MariTalk: "integrations.bundles.maritalk",
  CrewAI: "integrations.bundles.crewai",
  IBM: "integrations.bundles.ibm",
  VertexAI: "integrations.bundles.vertexai",
  Baidu: "integrations.bundles.baidu",
  AIML: "integrations.bundles.aiml",
  
  // ===========================================
  // Core Component Bundles
  // ===========================================
  LanguageModels: "integrations.bundles.languagemodels",
  Embeddings: "integrations.bundles.embeddings",
  Memories: "integrations.bundles.memories",
  VectorStores: "integrations.bundles.vectorstores",
  
  // ===========================================
  // Vector Store & Database Bundles
  // ===========================================
  Chroma: "integrations.bundles.chroma",
  Pinecone: "integrations.bundles.pinecone",
  Qdrant: "integrations.bundles.qdrant",
  Weaviate: "integrations.bundles.weaviate",
  Milvus: "integrations.bundles.milvus",
  Cassandra: "integrations.bundles.cassandra",
  DataStax: "integrations.bundles.datastax",
  Couchbase: "integrations.bundles.couchbase",
  ClickHouse: "integrations.bundles.clickhouse",
  MongoDB: "integrations.bundles.mongodb",
  Redis: "integrations.bundles.redis",
  Supabase: "integrations.bundles.supabase",
  Upstash: "integrations.bundles.upstash",
  Elastic: "integrations.bundles.elastic",
  FAISS: "integrations.bundles.faiss",
  pgvector: "integrations.bundles.pgvector",
  Vectara: "integrations.bundles.vectara",
  Mem0: "integrations.bundles.mem0",
  Zep: "integrations.bundles.zep",
  
  // ===========================================
  // Search & Web Services Bundles
  // ===========================================
  DuckDuckGo: "integrations.bundles.duckduckgo",
  Exa: "integrations.bundles.exa",
  Tavily: "integrations.bundles.tavily",
  SearchApi: "integrations.bundles.searchapi",
  SerpApi: "integrations.bundles.serpapi",
  Serper: "integrations.bundles.serper",
  Bing: "integrations.bundles.bing",
  Wikipedia: "integrations.bundles.wikipedia",
  WolframAlpha: "integrations.bundles.wolframalpha",
  YouTube: "integrations.bundles.youtube",
  YahooFinance: "integrations.bundles.yahoosearch",
  
  // ===========================================
  // Document/Content Processing Bundles
  // ===========================================
  Firecrawl: "integrations.bundles.firecrawl",
  ScrapeGraph: "integrations.bundles.scrapegraph",
  Unstructured: "integrations.bundles.unstructured",
  TwelveLabs: "integrations.bundles.twelvelabs",
  VLMRun: "integrations.bundles.vlmrun",
  Docling: "integrations.bundles.docling",
  
  // ===========================================
  // Developer Tools & Services Bundles
  // ===========================================
  Git: "integrations.bundles.git",
  LangChain: "integrations.bundles.langchain",
  Gmail: "integrations.bundles.gmail",
  Glean: "integrations.bundles.glean",
  Needle: "integrations.bundles.needle",
  NotDiamond: "integrations.bundles.notdiamond",
  Olivya: "integrations.bundles.olivya",
  HomeAssistant: "integrations.bundles.homeassistant",
  IcosaComputing: "integrations.bundles.icosacomputing",
  JigsawStack: "integrations.bundles.jigsawstack",
  
  // ===========================================
  // External Services Bundles
  // ===========================================
  Apify: "integrations.bundles.apify",
  AgentQL: "integrations.bundles.agentql",
  Confluence: "integrations.bundles.confluence",
  Notion: "integrations.bundles.notion",
  AssemblyAI: "integrations.bundles.assemblyai",
  Cloudflare: "integrations.bundles.cloudflare",
  Composio: "integrations.bundles.composio",
  arXiv: "integrations.bundles.arxiv",
  
  // ===========================================
  // Observability Bundles
  // NOTE: All observability (Langfuse, LangSmith, LangWatch) is mandatory/always-on
  // ===========================================
  CometAPI: "integrations.bundles.comet",
  Cleanlab: "integrations.bundles.cleanlab",
  
  // ===========================================
  // Specialized Bundles
  // ===========================================
  ALTK: "integrations.bundles.altk",
  CUGA: "integrations.bundles.cuga",
};

/**
 * Maps lowercase bundle names (from SIDEBAR_BUNDLES) to their capitalized keys in BUNDLE_FEATURES.
 * This handles the case-sensitivity mismatch between sidebar bundle names and feature map keys.
 */
const BUNDLE_NAME_MAP: Record<string, string> = {
  // ===========================================
  // AI/ML Provider Bundles
  // ===========================================
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  mistral: "Mistral",
  groq: "Groq",
  azure: "Azure",
  cohere: "Cohere",
  huggingface: "HuggingFace",
  ollama: "Ollama",
  amazon: "Amazon",
  aws: "AWS",
  deepseek: "DeepSeek",
  xai: "xAI",
  openrouter: "OpenRouter",
  perplexity: "Perplexity",
  novita: "Novita",
  nvidia: "NVIDIA",
  sambanova: "SambaNova",
  lmstudio: "LMStudio",
  maritalk: "MariTalk",
  crewai: "CrewAI",
  ibm: "IBM",
  vertexai: "VertexAI",
  baidu: "Baidu",
  aiml: "AIML",
  
  // ===========================================
  // Core Component Bundles
  // ===========================================
  languagemodels: "LanguageModels",
  embeddings: "Embeddings",
  memories: "Memories",
  vectorstores: "VectorStores",
  
  // ===========================================
  // Vector Store & Database Bundles
  // ===========================================
  chroma: "Chroma",
  pinecone: "Pinecone",
  qdrant: "Qdrant",
  weaviate: "Weaviate",
  milvus: "Milvus",
  cassandra: "Cassandra",
  datastax: "DataStax",
  couchbase: "Couchbase",
  clickhouse: "ClickHouse",
  mongodb: "MongoDB",
  redis: "Redis",
  supabase: "Supabase",
  upstash: "Upstash",
  elastic: "Elastic",
  faiss: "FAISS",
  pgvector: "pgvector",
  vectara: "Vectara",
  mem0: "Mem0",
  zep: "Zep",
  
  // ===========================================
  // Search & Web Services Bundles
  // ===========================================
  duckduckgo: "DuckDuckGo",
  exa: "Exa",
  tavily: "Tavily",
  searchapi: "SearchApi",
  serpapi: "SerpApi",
  serper: "Serper",
  bing: "Bing",
  wikipedia: "Wikipedia",
  wolframalpha: "WolframAlpha",
  youtube: "YouTube",
  yahoosearch: "YahooFinance",
  
  // ===========================================
  // Document/Content Processing Bundles
  // ===========================================
  firecrawl: "Firecrawl",
  scrapegraph: "ScrapeGraph",
  unstructured: "Unstructured",
  twelvelabs: "TwelveLabs",
  vlmrun: "VLMRun",
  docling: "Docling",
  
  // ===========================================
  // Developer Tools & Services Bundles
  // ===========================================
  git: "Git",
  langchain_utilities: "LangChain",
  gmail: "Gmail",
  glean: "Glean",
  needle: "Needle",
  notdiamond: "NotDiamond",
  olivya: "Olivya",
  homeassistant: "HomeAssistant",
  icosacomputing: "IcosaComputing",
  jigsawstack: "JigsawStack",
  
  // ===========================================
  // External Services Bundles
  // ===========================================
  apify: "Apify",
  agentql: "AgentQL",
  confluence: "Confluence",
  notion: "Notion",
  assemblyai: "AssemblyAI",
  cloudflare: "Cloudflare",
  composio: "Composio",
  arxiv: "arXiv",
  
  // ===========================================
  // Observability Bundles
  // NOTE: All observability (langfuse, langsmith, langwatch) is mandatory/always-on
  // ===========================================
  cometapi: "CometAPI",
  cleanlab: "Cleanlab",
  
  // ===========================================
  // Specialized Bundles
  // ===========================================
  altk: "ALTK",
  cuga: "CUGA",
};

/**
 * Normalizes a bundle name from sidebar format (lowercase) to BUNDLE_FEATURES key format (capitalized).
 * @param bundleName - The lowercase bundle name from SIDEBAR_BUNDLES
 * @returns The normalized bundle name for BUNDLE_FEATURES lookup, or the original name if not found
 */
export function normalizeBundleName(bundleName: string): string {
  return BUNDLE_NAME_MAP[bundleName.toLowerCase()] || bundleName;
}

// =============================================================================
// API FEATURE REQUIREMENTS
// =============================================================================

/**
 * Maps API operations to their required features.
 * Used for client-side validation before making API calls.
 */
export const API_OPERATION_FEATURES: Record<string, string[]> = {
  "execute-flow": [], // Basic execution always allowed
  "execute-flow-streaming": ["api.streaming_responses"],
  "execute-batch": ["api.batch_execution"],
  "create-webhook": ["api.webhooks"],
  "export-flow": ["ui.flow_builder.export_flow"],
  "import-flow": ["ui.flow_builder.import_flow"],
  "share-flow": ["ui.flow_builder.share_flow"],
  "create-api-key": ["ui.advanced.api_keys_management"],
  "create-custom-component": ["components.custom.enabled"],
  "edit-component-code": ["components.custom.code_editing"],
  "add-mcp-server": ["integrations.mcp"],
};

// =============================================================================
// UTILITY TYPES
// =============================================================================

export type FeatureMap = Record<string, string | string[]>;

/**
 * All feature maps combined for easy iteration.
 */
export const ALL_FEATURE_MAPS = {
  PROVIDER_FEATURE_MAP,
  COMPONENT_CATEGORY_FEATURES,
  SETTINGS_SIDEBAR_FEATURES,
  FLOW_TOOLBAR_FEATURES,
  NODE_TOOLBAR_FEATURES,
  DEBUG_FEATURES,
  INTEGRATION_FEATURES,
  COMPONENT_TYPE_FEATURES,
  SIDEBAR_SEGMENT_FEATURES,
  API_OPERATION_FEATURES,
  NAVIGATION_FEATURES,
  BUNDLE_FEATURES,
} as const;


