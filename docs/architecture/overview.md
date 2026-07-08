# Architecture Overview

ProjectLens AI follows a clean layered architecture with strict dependency direction. Each layer communicates only with the layer directly below it, ensuring a clear separation of concerns and testability.

---

## Layer Architecture

```
┌─────────────────────────────────────┐
│         Client Layer                │
│  (Next.js Frontend / API Clients)   │
└──────────────┬──────────────────────┘
               │ HTTP/REST
┌──────────────▼──────────────────────┐
│         API Layer                    │
│  (FastAPI v1, Auth, Middleware)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Core Layer                   │
│  (Workflows, Services, Repos)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          AI Layer                    │
│  (Chunking, Embedding, Retrieval,   │
│   LLM, Context, Prompting)           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Storage Layer                │
│  (PostgreSQL, Redis, Object Store)   │
└─────────────────────────────────────┘
```

### Client Layer
The topmost layer handles user interaction. The Next.js 14 frontend renders the UI and communicates with the API layer over HTTP/REST. External API clients also connect here.

### API Layer
Exposes a versioned REST API (`/api/v1`). Handles authentication, request validation, rate limiting, and routing. Controllers are thin — they delegate all business logic to the Core layer.

### Core Layer
Contains all business logic: workflows (orchestrating multi-step operations), services (single-responsibility business operations), and repositories (data access abstraction). This layer has no dependency on the API or AI layers.

### AI Layer
Provider-agnostic AI functionality: document chunking, text embedding, vector retrieval, LLM interaction, context assembly, and prompt management. Uses a plugin registry pattern to support multiple AI providers without switching logic.

### Storage Layer
Persistence and caching. PostgreSQL 16 with pgvector for relational data and vector embeddings. Redis for caching and task queues. Object storage for uploaded documents and analysis artifacts.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Layer-by-layer architecture** | Strict dependency direction enforces separation of concerns and makes the system testable. Each layer can be mocked or substituted independently. |
| **Plugin registry pattern** | AI providers are registered as plugins, eliminating if-else chains. Adding a new provider requires zero changes to consumer code. |
| **Async-first** | All I/O-bound operations (database queries, AI calls, file processing) are asynchronous, maximizing throughput under load. |
| **Provider-agnostic AI** | The AI layer defines abstract interfaces for embedding and LLM operations. Concrete implementations are injected via the registry. |
| **Versioned API** | All endpoints are prefixed with `/api/v1` to allow backward-compatible evolution of the public surface. |
