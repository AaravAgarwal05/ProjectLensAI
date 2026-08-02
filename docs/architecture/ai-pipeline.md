# AI Pipeline

End-to-end data flow: from an uploaded PDF/DOCX to a cited chat answer. Two pipelines — one
offline (ingest/index) and one online (RAG query). Each stage is provider-agnostic: strategies
and providers register behind a registry/factory, so swapping a provider never touches consumers.

---

## 1. Ingest pipeline (background, per report version)

Triggered by `POST /reports` and `POST /reports/{id}/versions` → `ProcessingService.process_report`
runs in the background (the API returns `201` immediately).

```
file → parse → clean → metadata → chunk → embed → index (Chroma)
 │       │        │          │        │       │        │
 │       parsers  cleaners  Metadata  Chunking Embedding VectorStore
 │       PDF/DOCX            Extractor Pipeline Pipeline IndexingEngine
 │       /Text               (title,   fixed/   (batch,  (batched,
 │                           lang,     recursive L2-norm) 3 retries)
 │                           counts)   heading_
 │                                      aware
 │
 ProcessingPipeline (document_processing/pipeline.py) with PipelineHook lifecycle
```

| Stage | Module | Notes |
|-------|--------|-------|
| Parse | `document_processing/parsers/` | PDF via PyMuPDF (encrypted rejected), DOCX via python-docx (20 MB bomb guard), TXT/MD/CSV. Registry lazy-instantiates |
| Clean | `document_processing/cleaners/` | `WhitespaceCleaner`, `UnicodeCleaner`, `PageArtifactCleaner` |
| Metadata | `document_processing/metadata.py` | title from filename, language heuristic, word/char counts |
| Chunk | `ai_core/chunking/` | strategy from user prefs — **default `heading_aware`**; also `fixed` / `recursive`. Config: size 1000, overlap 200, min 100 |
| Embed | `ai_core/embedding/` | provider from `build_embedding_provider()` — **default gemini** (`text-embedding-004`, 768-dim, L2-normalized). Also ollama (`nomic-embed-text`), sentence_transformer (local) |
| Index | `ai_core/vector_store/` | Chroma collection `report_{id}`; metadata carries `chunk_id`, `report_id`, `version_id`, `embedding_model`, `provider` |

**Failure path:** any stage error → report status `error` with a message; tempfile cleaned in a
`finally`.

> ⚠️ **Provider mismatch to know about:** the ingest path reads embedding provider from the
> user's stored `preferences` (default `ollama`), while the chat path builds its own embed
> provider (default `gemini`). If the two differ, the query embedding space may not match the
> indexed one. Aligning the default (see [Database](../database/overview.md#users)) removes this.

---

## 2. Query pipeline (per chat message)

`POST /chat/send` (JSON) or `POST /chat/send/stream` (SSE) → `ChatOrchestrator.process_message[_streaming]`.

```
message + session report_ids
   │
   ▼
1. validate + save user message
   ▼
2. load history (≤ 50 messages)
   ▼
3. query rewrite ── when history ≥ 3 msgs (LLM)
   ▼
4. retrieve ── embed query ──▶ Chroma query per report ──▶ rerank (MMR λ=0.4, top_k 25)
   │
   ▼
5. context assembly ── TokenBudgetManager allocate + enforce
   │
   ▼
6. prompt build (PromptBuilder: system + [Chunk N] sections, prompt_hash)
   ▼
7. LLM generate (opencode_zen default) ── streaming when /send/stream
   ▼
8. citations (CitationEngine: dedupe by chunk_id, max 10)
   ▼
9. save assistant message ── regenerate session summary when ≥ 6 msgs
   ▼
10. persist RequestTrace (fire-and-forget)
```

### Stage detail

| # | Stage | Where | Details |
|---|-------|-------|---------|
| 3 | Query rewrite | `ai_core/chat/orchestrator.py` | for multi-turn conversations, rewrites the query with conversation context |
| 4 | Retrieve | `ai_core/retrieval/` | `RetrievalPipeline`: dense (vector) by default; `HybridRetriever` adds inline BM25 (k1=1.2, b=0.75); multi_query expands the query. Rerankers: MMR (default in chat, λ=0.4), cross-encoder (ms-marco-MiniLM-L-6-v2, graceful fallback) |
| 5 | Context | `ai_core/context/` | `ContextAssemblyPipeline`: chunk selection strategy (`single_document` default — strict-grounding prompt, top 20), metadata enrichment, conversation manager, `TokenBudgetManager` |
| 6 | Prompt | `ai_core/llm/prompt_builder.py` | system prompt (incl. prompt-injection defense) + `[Chunk N]` user sections; computes `sha256[:16]` prompt_hash |
| 7 | LLM | `ai_core/llm/` | `build_llm_provider()` → default `opencode_zen` / `deepseek-v4-flash-free` (free tier). Fallbacks: `fallback` provider wraps Ollama (`llama3.2:1b`), then Google (Gemini). Streamed via SSE `{type: 'token'|'done'|'error'}` |
| 8 | Citations | `ai_core/chat/citations.py` | `CitationEngine` maps cited chunk ids → source refs (report, section, page) |

### The fallback path

When the orchestrator path is unavailable, `chat.py` falls back to
`RAGChatService.answer()`: embed the query once (Redis-cached `embedding:{sha256}`, 1h TTL),
query Chroma per report in a thread, assemble context, generate. It also persists a
`RequestTrace`.

---

## 3. Observability

Every chat turn emits a **`RequestTrace`** (`ai_core/tracing/`): request identity (`request_id`,
`user_id`, `session_id`), LLM identity (`model`, `provider`, `prompt_version`, `prompt_hash`,
`cache_hit`), per-stage latencies (rewrite / embed / retrieve / context / prompt_build / llm /
save / total), and counts (chunks retrieved/cited, tokens). Persisted to `request_traces` via
`TraceStore` fire-and-forget — failures are swallowed so tracing never breaks chat.

**Evaluation** (`scripts/eval_rag.py` + `ai_core/eval/`): runs a query set through the pipeline,
scores answers with an LLM judge, and POSTs the run (config snapshot + metrics + per-query
results) to `/api/v1/eval/runs` → `eval_runs` table. Combined with traces, this makes quality
and latency attributable to a `prompt_version` / model / retrieval config.

---

## 4. Provider matrix

| Concern | Default | Alternatives | Selection point |
|---------|---------|--------------|-----------------|
| Chunking | `heading_aware` | `fixed`, `recursive` | user prefs → `build_chunker` |
| Embedding (ingest) | `ollama` (per user prefs) | `gemini`, `sentence_transformer` | user prefs |
| Embedding (chat) | `gemini` | `ollama`, `sentence_transformer` | `build_embedding_provider()` |
| Vector store | Chroma | PgVector (not wired) | `VectorStoreConfiguration` |
| Retrieval | dense | hybrid (BM25), multi_query | `RetrieverConfiguration` |
| Reranker | none (MMR in chat) | cross-encoder | `build_reranker` |
| Context strategy | `single_document` | multi_document, comparison, summary | `ContextConfiguration` |
| LLM | `opencode_zen` / `deepseek-v4-flash-free` | google, ollama, fallback | `build_llm_provider()` |

Each provider implements an ABC (`LLMProvider`, `EmbeddingProvider`, `BaseChunker`, …) and is
registered in a registry; consumers depend only on the ABC. See
[Backend Services](../backend/services.md#ai_core--the-rag-engine).
