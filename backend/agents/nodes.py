"""
Agent Nodes (Phase 9) — individual LangGraph node functions.

Each node receives an AgentState and returns a partial state dict.
Nodes are pure async functions; side-effects (LLM calls, retrieval) are
injected via the NodeDependencies bundle so tests can mock them easily.

Nodes in the graph
──────────────────
  route_query      → decides retrieval strategy (hybrid/faiss/bm25)
  rewrite_query    → rewrites a vague or low-quality query
  retrieve         → runs the chosen retrieval strategy
  grade_documents  → scores each chunk for relevance; drops poor ones
  generate         → calls the LLM to produce an answer
  check_grounding  → verifies the answer is grounded in the documents
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from backend.agents.state import AgentState
from backend.core.settings import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


# ── Routing classifier prompts ────────────────────────────────────────────

_ROUTE_PROMPT = """\
You are a query router for a document retrieval system.  Given the user \
question below, choose the best retrieval strategy.

Strategies:
- hybrid   : best overall; combines semantic + keyword search
- faiss    : good when the question is conceptual or requires paraphrasing
- bm25     : good when the question contains exact technical terms or codes

Respond with exactly one word: hybrid, faiss, or bm25.

Question: {query}

Strategy:"""

_REWRITE_PROMPT = """\
You are a helpful assistant.  The query below may be vague, ambiguous, or \
too short.  Rewrite it as a clear, self-contained question that will produce \
better search results.  Return only the rewritten question, nothing else.

Original query: {query}

Rewritten query:"""

_GRADE_PROMPT = """\
You are a relevance grader.  Assess whether the document excerpt below is \
relevant to the question.

Question: {query}
Document excerpt: {content}

Respond with exactly one word: yes or no.

Relevant:"""

_GROUND_PROMPT = """\
You are a strict fact-checker.  Does the answer below rely only on \
information from the context provided?  If there are claims not supported \
by the context, respond HALLUCINATION.  Otherwise respond GROUNDED.

Context:
{context}

Answer: {answer}

Verdict:"""


# ── Node: route_query ─────────────────────────────────────────────────────

async def route_query(state: AgentState, llm) -> Dict[str, Any]:
    """
    Use the LLM to pick the best retrieval strategy for the query.

    Falls back to ``settings.default_retrieval_method`` on any error.
    """
    query = state.get("rewritten_query") or state["query"]
    start = time.time()

    try:
        result = await llm.generate(
            prompt=_ROUTE_PROMPT.format(query=query),
            temperature=0.0,
            max_tokens=5,
        )
        strategy = result.get("text", "").strip().lower()
        if strategy not in ("hybrid", "faiss", "bm25"):
            strategy = settings.default_retrieval_method
    except Exception as e:
        logger.warning(f"route_query LLM call failed ({e}), using default strategy")
        strategy = settings.default_retrieval_method

    logger.info(f"route_query → {strategy} ({time.time()-start:.2f}s)")
    return {
        "retrieval_method": strategy,
        "trace": [f"route_query: strategy={strategy}"],
    }


# ── Node: rewrite_query ───────────────────────────────────────────────────

async def rewrite_query(state: AgentState, llm) -> Dict[str, Any]:
    """
    Rewrite the query to improve retrieval quality.
    Increments the rewrite counter (used as a loop guard).
    """
    query = state["query"]
    count = state.get("rewrite_count", 0)
    start = time.time()

    try:
        result = await llm.generate(
            prompt=_REWRITE_PROMPT.format(query=query),
            temperature=0.3,
            max_tokens=80,
        )
        rewritten = result.get("text", "").strip() or query
    except Exception as e:
        logger.warning(f"rewrite_query failed ({e}), keeping original")
        rewritten = query

    logger.info(f"rewrite_query: '{query}' → '{rewritten}' ({time.time()-start:.2f}s)")
    return {
        "rewritten_query": rewritten,
        "rewrite_count":   count + 1,
        "trace": [f"rewrite_query: count={count+1} rewritten='{rewritten[:60]}'"],
    }


# ── Node: retrieve ────────────────────────────────────────────────────────

async def retrieve(state: AgentState, retriever) -> Dict[str, Any]:
    """
    Run the chosen retrieval strategy and return raw documents.

    ``retriever`` is a HybridRetriever instance.
    """
    query  = state.get("rewritten_query") or state["query"]
    method = state.get("retrieval_method", settings.default_retrieval_method)
    top_k  = state.get("top_k", settings.top_k_retrieval)
    start  = time.time()

    try:
        results = await retriever.retrieve(
            query=query,
            top_k=top_k,
            method=method,
        )
        # Serialize to plain dicts so state is JSON-compatible
        docs = [
            {
                "chunk_id":         r.chunk_id,
                "content":          r.content,
                "score":            r.score,
                "document_id":      r.document_id,
                "filename":         r.filename,
                "page_number":      r.page_number,
                "retrieval_method": getattr(r, "retrieval_method", method),
                "faiss_score":      getattr(r, "faiss_score", None),
                "bm25_score":       getattr(r, "bm25_score", None),
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"retrieve failed: {e}")
        docs = []

    logger.info(
        f"retrieve: method={method} top_k={top_k} "
        f"got={len(docs)} docs ({time.time()-start:.2f}s)"
    )
    return {
        "documents": docs,
        "trace": [f"retrieve: method={method} docs={len(docs)}"],
    }


# ── Node: grade_documents ─────────────────────────────────────────────────

async def grade_documents(state: AgentState, llm) -> Dict[str, Any]:
    """
    Score each retrieved chunk for relevance and filter out poor ones.

    Kept chunks must score "yes" from the LLM relevance grader.
    If no LLM is available (or too slow), pass all documents through.
    """
    query = state.get("rewritten_query") or state["query"]
    docs  = state.get("documents", [])
    start = time.time()

    if not docs:
        return {"documents": [], "trace": ["grade_documents: no docs to grade"]}

    # Skip LLM grading if disabled in settings
    if not settings.agent_enable_document_grading:
        return {"documents": docs, "trace": [f"grade_documents: skipped (disabled), kept {len(docs)}"]}

    graded = []
    for doc in docs:
        try:
            result = await llm.generate(
                prompt=_GRADE_PROMPT.format(query=query, content=doc["content"][:500]),
                temperature=0.0,
                max_tokens=5,
            )
            verdict = result.get("text", "").strip().lower()
            if verdict.startswith("yes"):
                graded.append(doc)
        except Exception:
            graded.append(doc)  # keep on error

    # Always keep at least 1 document to avoid empty context
    if not graded and docs:
        graded = docs[:1]

    logger.info(
        f"grade_documents: kept {len(graded)}/{len(docs)} docs "
        f"({time.time()-start:.2f}s)"
    )
    return {
        "documents": graded,
        "trace": [f"grade_documents: kept={len(graded)}/{len(docs)}"],
    }


# ── Node: generate ────────────────────────────────────────────────────────

_GENERATE_PROMPT = """\
You are a helpful AI assistant that answers questions based on the provided \
context.  Always cite your sources by referring to document names and page \
numbers when available.  If the context does not contain enough information, \
say so clearly.  Be concise and accurate.

{history_section}
Context from documents:
{context}

Question: {query}

Answer:"""


async def generate(state: AgentState, llm) -> Dict[str, Any]:
    """Generate an answer from the retrieved and graded documents."""
    query   = state.get("rewritten_query") or state["query"]
    docs    = state.get("documents", [])
    history = state.get("conversation_history", [])
    start   = time.time()

    # Build context string
    context_parts = []
    for i, doc in enumerate(docs, 1):
        fn   = doc.get("filename", "unknown")
        pg   = doc.get("page_number")
        pg_s = f" (p.{pg})" if pg else ""
        context_parts.append(f"[{i}] {fn}{pg_s}\n{doc['content']}")
    context = "\n\n".join(context_parts) if context_parts else "No context available."

    # Build history section
    history_section = ""
    if history:
        lines = []
        for m in history[-6:]:  # last 6 messages
            role = m.get("role", "user")
            lines.append(f"{role.capitalize()}: {m.get('content', '')}")
        history_section = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    prompt = _GENERATE_PROMPT.format(
        history_section=history_section,
        context=context,
        query=query,
    )

    try:
        result = await llm.generate(
            prompt=prompt,
            temperature=state.get("temperature", 0.7),
            max_tokens=state.get("max_tokens", 500),
        )
        answer = result.get("text", "").strip()
        model  = result.get("model", "unknown")
        tokens = result.get("tokens_used", 0)
    except Exception as e:
        logger.error(f"generate failed: {e}")
        answer = "I'm sorry, I was unable to generate a response at this time."
        model  = "unknown"
        tokens = 0

    logger.info(f"generate: {len(answer)} chars ({time.time()-start:.2f}s)")
    return {
        "generation": answer,
        "metadata":   {
            **(state.get("metadata") or {}),
            "model":           model,
            "tokens_used":     tokens,
            "generation_time": round(time.time() - start, 3),
        },
        "trace": [f"generate: len={len(answer)} model={model}"],
    }


# ── Node: check_grounding ─────────────────────────────────────────────────

async def check_grounding(state: AgentState, llm) -> Dict[str, Any]:
    """
    Verify the answer is supported by the retrieved context.
    Sets ``is_grounded`` in the state.
    """
    answer = state.get("generation", "")
    docs   = state.get("documents", [])
    start  = time.time()

    if not docs or not answer:
        return {
            "is_grounded": True,  # nothing to check → pass
            "trace": ["check_grounding: skipped (no docs/answer)"],
        }

    if not settings.agent_enable_grounding_check:
        return {
            "is_grounded": True,
            "trace": ["check_grounding: skipped (disabled)"],
        }

    context = "\n\n".join(d["content"][:400] for d in docs[:3])
    try:
        result = await llm.generate(
            prompt=_GROUND_PROMPT.format(context=context, answer=answer[:800]),
            temperature=0.0,
            max_tokens=10,
        )
        verdict = result.get("text", "").strip().upper()
        grounded = "HALLUCINATION" not in verdict
    except Exception as e:
        logger.warning(f"check_grounding LLM call failed ({e}), assuming grounded")
        grounded = True

    logger.info(
        f"check_grounding: grounded={grounded} ({time.time()-start:.2f}s)"
    )
    return {
        "is_grounded": grounded,
        "trace": [f"check_grounding: grounded={grounded}"],
    }


# Made with Bob
