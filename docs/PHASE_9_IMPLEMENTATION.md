# Phase 9 — Agentic RAG: Implementation Summary

## Overview

Phase 9 adds a full **LangGraph state machine** to the platform, turning the linear RAG pipeline into an adaptive agentic workflow. Instead of always applying the same retrieval strategy, the agent:

1. **Routes** each query to the most appropriate retrieval method
2. **Rewrites** vague or ambiguous queries before retrieval
3. **Grades** each retrieved chunk for relevance before generation
4. **Verifies** that the generated answer is grounded in the retrieved context
5. **Loops** back if grounding fails and rewrite budget remains

---

## Architecture

### Graph Flow

```
                    ┌─────────────────────┐
                    │        START         │
                    └──────────┬──────────┘
                               ▼
                         route_query          ← LLM picks hybrid | faiss | bm25
                               │
            ┌──────────────────┼──────────────────────┐
            │  first run &     │                       │
            │  count < max     │  already rewritten    │
            ▼                  │  or at max            │
      rewrite_query            │                       │
            │                  │                       │
            └──────────────────┘                       │
                               │                       │
                               ▼                       │
                            retrieve ◄─────────────────┘
                               │
                        grade_documents       ← drops irrelevant chunks
                               │
                            generate          ← builds answer from kept chunks
                               │
                        check_grounding       ← verifies answer vs context
                               │
            ┌──────────────────┼──────────────────────┐
            │  grounded OR     │                       │
            │  max rewrites    │  hallucination +      │
            │  reached         │  budget remains       │
            ▼                  │                       │
           END                 └──────▶ route_query ──┘
                                          (retry loop)
```

### Node responsibilities

| Node | LLM calls | What it does |
|------|-----------|-------------|
| `route_query` | 1 | Classifies query → picks `hybrid`, `faiss`, or `bm25` |
| `rewrite_query` | 1 | Rewrites vague query for better retrieval quality |
| `retrieve` | 0 | Calls `HybridRetriever.retrieve()` with chosen strategy |
| `grade_documents` | N (1 per chunk) | Scores each chunk yes/no; drops irrelevant ones |
| `generate` | 1 | Generates answer from graded context + history |
| `check_grounding` | 1 | Verifies answer only uses retrieved context |

### Conditional edges

| From | Condition | To |
|------|-----------|----|
| `route_query` | `rewrite_count == 0` and no `rewritten_query` | `rewrite_query` |
| `route_query` | Already rewritten or at max | `retrieve` |
| `check_grounding` | `is_grounded == True` or at max rewrites | `END` |
| `check_grounding` | `is_grounded == False` and budget remains | `route_query` |

---

## Files Created

### Backend

| File | Description |
|------|-------------|
| `backend/agents/state.py` | `AgentState` TypedDict — the shared state passed between all nodes |
| `backend/agents/nodes.py` | Pure async node functions: `route_query`, `rewrite_query`, `retrieve`, `grade_documents`, `generate`, `check_grounding` |
| `backend/agents/graph.py` | `AgentGraph` class — builds and compiles the LangGraph `StateGraph`; exposes `async run(initial_state)` |
| `backend/agents/__init__.py` | Re-exports `AgentState` and `AgentGraph` |
| `backend/api/routes/agent.py` | FastAPI router: `POST /api/v1/agent/chat`, `GET /api/v1/agent/health` |

### Frontend

| File | Description |
|------|-------------|
| `frontend/streamlit/pages/4_🤖_Agent.py` | Agentic Chat UI — shows answer, sources, graph trace, retrieval strategy, rewrite count, and grounding verdict |

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `AGENT_ENABLE_DOCUMENT_GRADING` | `true` | LLM grades each retrieved chunk for relevance |
| `AGENT_ENABLE_GROUNDING_CHECK` | `true` | Post-generation grounding verification |
| `AGENT_MAX_REWRITES` | `2` | Maximum query rewrite iterations (loop guard) |

---

## API

### `POST /api/v1/agent/chat`

**Request body:**
```json
{
  "message": "What are the key findings?",
  "conversation_id": "agent_abc123",
  "top_k": 5,
  "temperature": 0.7,
  "max_tokens": 500,
  "retrieval_method": null,
  "use_reranking": false,
  "conversation_history": []
}
```

**Response:**
```json
{
  "conversation_id": "agent_abc123",
  "answer": "The key findings are...",
  "sources": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "filename": "report.pdf",
      "content": "...",
      "score": 0.847,
      "page_number": 3,
      "retrieval_method": "hybrid",
      "faiss_score": 0.91,
      "bm25_score": 0.72
    }
  ],
  "retrieval_method": "hybrid",
  "is_grounded": true,
  "rewrite_count": 1,
  "rewritten_query": "What are the primary conclusions and findings in the document?",
  "trace": [
    "route_query: strategy=hybrid",
    "rewrite_query: count=1 rewritten='What are the primary conclusions...'",
    "retrieve: method=hybrid docs=5",
    "grade_documents: kept=4/5",
    "generate: len=312 model=qwen3:4b",
    "check_grounding: grounded=True"
  ],
  "model": "qwen3:4b",
  "tokens_used": 847,
  "processing_time": 12.4
}
```

### `GET /api/v1/agent/health`

```json
{
  "status": "healthy",
  "graph": "compiled",
  "max_rewrites": 2,
  "document_grading": true,
  "grounding_check": true
}
```

---

## Design Decisions

### Why LangGraph?
LangGraph's `StateGraph` provides:
- **Typed shared state** — `AgentState` TypedDict prevents field name typos
- **Conditional edges** — clean loop and branch logic without nested if-else
- **Async-native** — `ainvoke()` integrates naturally with FastAPI's async event loop
- **Trace-friendly** — each node appends to the `trace` list via `operator.add`

### Why pure node functions (not methods)?
Each node is a plain `async def` accepting `(state, dependency)`. This makes unit testing trivial — mock the LLM or retriever, call the function, assert on the returned dict.

### Why not replace the existing `/api/v1/chat`?
The linear `RAGChain` and the agentic `AgentGraph` serve different use cases:
- `/chat` — fast, single-pass, streaming-compatible, low latency
- `/agent/chat` — adaptive, multi-pass, higher accuracy, higher latency

Both are kept so the frontend can let the user choose.

---

## Performance Notes

On CPU-only Ollama (`qwen3:4b`), each agent run makes 3–6 LLM calls:

| Config | LLM calls | Typical latency |
|--------|-----------|-----------------|
| Grading off, grounding off | 2 (route + generate) | 30–90 s |
| Grading on, grounding off | 2 + N chunks | 60–180 s |
| Full (default) | 3–6 | 90–300 s |

To reduce latency during development, set in `.env`:
```env
AGENT_ENABLE_DOCUMENT_GRADING=false
AGENT_ENABLE_GROUNDING_CHECK=false
AGENT_MAX_REWRITES=0
```

---

**Phase**: 9
**Status**: ✅ Complete
**Date**: 2026-07-01
