"""
Agent State (Phase 9) — LangGraph state definition.

All data flowing through the agentic RAG graph lives in AgentState.
LangGraph passes this dict between nodes; each node returns a partial
dict that is merged into the running state.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
import operator


class AgentState(TypedDict, total=False):
    """
    Shared state for the Agentic RAG LangGraph.

    Fields
    ------
    query               Original user question (never mutated).
    rewritten_query     LLM-rewritten query (set by the rewrite node).
    retrieval_method    Chosen retrieval strategy: hybrid | faiss | bm25.
    use_reranking       Whether to apply cross-encoder reranking.
    top_k               Number of chunks to retrieve.
    documents           Retrieved chunks (list of HybridRetrievalResult-like dicts).
    generation          LLM-generated answer text.
    is_grounded         Output of the grounding check node (True/False).
    rewrite_count       How many times the query has been rewritten (loop guard).
    conversation_history  Prior messages for prompt context.
    temperature         LLM temperature.
    max_tokens          Max generation tokens.
    metadata            Any extra metadata to return to the caller.
    # Accumulate log entries across nodes for observability
    trace               List of trace strings; each node appends its entry.
    """
    query:                str
    rewritten_query:      Optional[str]
    retrieval_method:     str
    use_reranking:        bool
    top_k:                int
    documents:            List[Dict[str, Any]]
    generation:           Optional[str]
    is_grounded:          Optional[bool]
    rewrite_count:        int
    conversation_history: List[Dict[str, str]]
    temperature:          float
    max_tokens:           int
    metadata:             Dict[str, Any]
    # Append-only via operator.add so multiple nodes can write safely
    trace:                Annotated[List[str], operator.add]


# Made with Bob
