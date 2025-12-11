<!-- markdownlint-disable MD030 -->




**Kluisz Kanvas** is a visual platform for building, deploying, and managing AI-powered workflows and agents. Create complex AI applications through an intuitive drag-and-drop interface, then deploy them as APIs or integrate them into any application stack.

## Platform Capabilities

### Visual Workflow Builder
Build AI workflows visually by connecting pre-built components. No code required to get started—drag, drop, and configure components to create sophisticated AI applications in minutes.

### Multi-Agent Orchestration
Design and orchestrate multi-agent systems with conversation management, retrieval capabilities, and complex agent interactions. Build agentic applications that can collaborate, reason, and solve complex tasks.

### LLM & Model Support
Connect to all major language models and AI providers:
- **OpenAI** (GPT-4, GPT-3.5, and more)
- **Anthropic** (Claude models)
- **Google** (Gemini, Vertex AI)
- **Mistral AI**
- **Groq**
- **Ollama** (local models)
- **Hugging Face**
- **Azure OpenAI**
- **AWS Bedrock**
- And many more via LiteLLM

### Vector Database Integration
Store and retrieve embeddings with support for:
- **Chroma**
- **Qdrant**
- **Weaviate**
- **Pinecone**
- **FAISS**
- **Milvus**
- **PostgreSQL** (pgvector)
- **MongoDB Atlas**
- **Redis**
- **Elasticsearch**
- **Astra DB**
- **Supabase**
- **Upstash Vector**

### Custom Components
Extend the platform with custom Python components. Access source code for all components and build your own reusable components tailored to your specific needs.

### Interactive Playground
Test and refine your workflows in real-time with the built-in playground. Iterate quickly with step-by-step execution control and immediate feedback.

### Deployment Options
Deploy your workflows in multiple ways:
- **REST API** - Turn any workflow into a production-ready API endpoint
- **MCP Server** - Expose workflows as tools via Model Context Protocol
- **JSON Export** - Export workflows for integration into Python applications
- **Command Line** - Run workflows directly via the `klx` CLI tool

### Observability & Monitoring
Monitor and debug your AI workflows with integrations for:
- **LangSmith** - Tracing and debugging
- **LangFuse** - LLM observability
- **LangWatch** - Performance monitoring
- **OpenTelemetry** - Standard observability protocols

### Data Processing & Integration
Process and integrate data from various sources:
- Document loaders (PDF, Word, Excel, and more)
- Web scraping and crawling
- Database connectors
- API integrations
- File processing
- Text extraction and parsing

### Enterprise Features
- **Multi-tenant architecture** - Isolated workspaces and data
- **Role-based access control** - Granular permissions
- **Security** - Enterprise-grade security features
- **Scalability** - Built to scale from prototype to production

## Quick Start

### Prerequisites
- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended package manager)

### Installation

```shell
uv pip install langflow -U
```

### Run

```shell
uv run langflow run
```

Kluisz Kanvas will be available at http://127.0.0.1:7860

## Installation Options

### From Source

If you've cloned this repository:

```shell
make run_cli
```

For development setup, see [DEVELOPMENT.md](./DEVELOPMENT.md).

### Docker

```shell
docker run -p 7860:7860 langflowai/langflow:latest
```

Access Kluisz Kanvas at http://localhost:7860/

> [!CAUTION]
> - Langflow versions 1.6.0 through 1.6.3 have a critical bug where `.env` files are not read, potentially causing security vulnerabilities. **DO NOT** upgrade to these versions if you use `.env` files for configuration. Instead, upgrade to 1.6.4, which includes a fix for this bug.
> - Windows users of the upstream Langflow Desktop should **not** use the in‑app update feature to upgrade to Langflow version 1.6.0. For upgrade instructions, see [Windows Desktop update issue](https://docs.langflow.org/release-notes#windows-desktop-update-issue).
> - Users must update to Langflow >= 1.3 to protect against [CVE-2025-3248](https://nvd.nist.gov/vuln/detail/CVE-2025-3248).
> - Users must update to Langflow >= 1.5.1 to protect against [CVE-2025-57760](https://github.com/langflow-ai/langflow/security/advisories/GHSA-4gv9-mp8m-592r).
>
> For security information, see our [Security Policy](./SECURITY.md) and [Security Advisories](https://github.com/langflow-ai/langflow/security/advisories).

## Deployment

Kluisz Kanvas is built on the open‑source Langflow engine and can be deployed to all major cloud platforms. For deployment guides, see the [Langflow deployment documentation](https://docs.langflow.org/deployment-overview).

## Documentation

Comprehensive documentation is available at [docs.kluisz.com](https://docs.kluisz.com).

## Contributing

We welcome contributions from developers of all levels. Please check our [contributing guidelines](./CONTRIBUTING.md) to get started.



---

> **Attribution**  
> Kluisz Kanvas is built on the open‑source [Langflow](https://github.com/langflow-ai/langflow) project and would not be possible without its maintainers and contributors.
# kluisz-ai-canvas
