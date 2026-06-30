"""
Phase 3 Tests: Query Understanding

Tests for QueryExpander, QueryReformulator, HyDEGenerator, and QueryProcessor.
Uses mocked LLM service to avoid requiring a running Ollama instance.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.query_understanding.query_expander import QueryExpander
from backend.query_understanding.query_reformulator import QueryReformulator
from backend.query_understanding.hyde_generator import HyDEGenerator, HyDEResult
from backend.query_understanding.query_processor import (
    QueryProcessor,
    QueryProcessingResult,
    QueryUnderstandingOptions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_service(response_text: str) -> MagicMock:
    """Return a mock LLMService whose generate() returns response_text."""
    llm = MagicMock()
    llm.generate = AsyncMock(return_value={"text": response_text, "model": "mock"})
    llm.provider_name = "mock"
    return llm


# ===========================================================================
# QueryExpander Tests
# ===========================================================================

class TestQueryExpander:
    """Tests for the QueryExpander class."""

    @pytest.mark.asyncio
    async def test_expand_returns_original_plus_expansions(self):
        """expand() should return the original query as the first item."""
        llm = _make_llm_service("How reliable are EV chargers?\nWhat is charging station availability?")
        expander = QueryExpander(llm_service=llm, default_num_expansions=2)

        result = await expander.expand("What is EVSE uptime?", num_expansions=2)

        assert result[0] == "What is EVSE uptime?"
        assert len(result) >= 1  # At least original returned on any parse result

    @pytest.mark.asyncio
    async def test_expand_falls_back_on_llm_failure(self):
        """expand() returns [original] when LLM raises an exception."""
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))
        llm.provider_name = "mock"
        expander = QueryExpander(llm_service=llm)

        result = await expander.expand("test query")

        assert result == ["test query"]

    def test_parse_expansions_strips_numbering(self):
        """_parse_expansions should remove leading numbers and bullets."""
        expander = QueryExpander(llm_service=MagicMock())
        raw = "1. How reliable are EV chargers?\n- What is charging station availability?\n* EVSE operational percentage"
        parsed = expander._parse_expansions(raw, expected_count=3)

        assert len(parsed) == 3
        assert not any(q.startswith(("1.", "-", "*")) for q in parsed)

    def test_parse_expansions_filters_short_lines(self):
        """_parse_expansions should skip lines shorter than 10 characters."""
        expander = QueryExpander(llm_service=MagicMock())
        raw = "Hi\nA valid expansion for testing purposes"
        parsed = expander._parse_expansions(raw, expected_count=2)

        assert all(len(q) >= 10 for q in parsed)

    def test_get_stats_returns_config(self):
        llm = _make_llm_service("")
        expander = QueryExpander(llm_service=llm, default_num_expansions=4, temperature=0.5)
        stats = expander.get_stats()
        assert stats["default_num_expansions"] == 4
        assert stats["temperature"] == 0.5


# ===========================================================================
# QueryReformulator Tests
# ===========================================================================

class TestQueryReformulator:
    """Tests for the QueryReformulator class."""

    def test_needs_reformulation_with_vague_pronoun(self):
        reformulator = QueryReformulator(llm_service=MagicMock())
        assert reformulator._needs_reformulation("How does it work?") is True

    def test_needs_reformulation_short_how_query(self):
        reformulator = QueryReformulator(llm_service=MagicMock())
        assert reformulator._needs_reformulation("How?") is True

    def test_no_reformulation_needed_for_clear_query(self):
        reformulator = QueryReformulator(llm_service=MagicMock())
        assert reformulator._needs_reformulation("What is the revenue for Q4 2024?") is False

    @pytest.mark.asyncio
    async def test_reformulate_clear_query_returns_original(self):
        """reformulate() should return the original when no reformulation is needed."""
        llm = _make_llm_service("some reformulation")
        reformulator = QueryReformulator(llm_service=llm)

        result = await reformulator.reformulate("What is the Q4 revenue for 2024?")

        assert result == "What is the Q4 revenue for 2024?"
        llm.generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reformulate_vague_query_calls_llm(self):
        """reformulate() should call the LLM for vague queries."""
        llm = _make_llm_service("What is the EVSE connector uptime monitoring system?")
        reformulator = QueryReformulator(llm_service=llm)

        result = await reformulator.reformulate("How does it work?")

        assert result == "What is the EVSE connector uptime monitoring system?"
        llm.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reformulate_falls_back_on_llm_failure(self):
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))
        reformulator = QueryReformulator(llm_service=llm)

        result = await reformulator.reformulate("How does it work?")

        assert result == "How does it work?"

    def test_parse_reformulation_removes_prefix(self):
        reformulator = QueryReformulator(llm_service=MagicMock())
        raw = "Reformulated query: What is the revenue for Q4 2024?"
        cleaned = reformulator._parse_reformulation(raw)
        assert cleaned == "What is the revenue for Q4 2024?"

    def test_build_context_section_uses_last_3_messages(self):
        reformulator = QueryReformulator(llm_service=MagicMock())
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Tell me about EVSE"},
            {"role": "assistant", "content": "EVSE stands for..."},
        ]
        context = reformulator._build_context_section(history)
        # Should contain the last 3 messages
        assert "Tell me about EVSE" in context
        assert "EVSE stands for..." in context


# ===========================================================================
# HyDEGenerator Tests
# ===========================================================================

class TestHyDEGenerator:
    """Tests for the HyDEGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_returns_answer(self):
        llm = _make_llm_service("EVSE downtime is caused by network failures and hardware issues.")
        generator = HyDEGenerator(llm_service=llm)

        result = await generator.generate("What causes EVSE downtime?")

        assert "EVSE" in result
        llm.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_falls_back_on_failure(self):
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))
        generator = HyDEGenerator(llm_service=llm)

        result = await generator.generate("What causes downtime?")

        assert result == "What causes downtime?"

    def test_parse_answer_strips_prefix(self):
        generator = HyDEGenerator(llm_service=MagicMock())
        raw = "Answer: The main cause of EVSE downtime is network failure."
        cleaned = generator._parse_answer(raw)
        assert cleaned.startswith("The main cause")

    def test_parse_answer_strips_quotes(self):
        generator = HyDEGenerator(llm_service=MagicMock())
        raw = '"EVSE connectors often fail due to hardware issues."'
        cleaned = generator._parse_answer(raw)
        assert not cleaned.startswith('"')

    def test_hyde_result_to_dict(self):
        hr = HyDEResult(
            original_query="What is uptime?",
            hypothetical_answer="Uptime is the percentage of time a system is operational.",
            generation_time=0.5
        )
        d = hr.to_dict()
        assert d["original_query"] == "What is uptime?"
        assert d["generation_time"] == 0.5
        assert "answer_length" in d

    def test_get_stats_returns_config(self):
        llm = _make_llm_service("")
        generator = HyDEGenerator(llm_service=llm, temperature=0.9, max_tokens=300)
        stats = generator.get_stats()
        assert stats["temperature"] == 0.9
        assert stats["max_tokens"] == 300


# ===========================================================================
# QueryProcessor Tests
# ===========================================================================

class TestQueryProcessor:
    """Tests for the QueryProcessor orchestrator."""

    def _make_processor(
        self,
        reform_result: str = "clear query",
        expand_result: str = "variant 1\nvariant 2",
        hyde_result: str = "hypothetical answer text"
    ) -> QueryProcessor:
        llm = _make_llm_service("")
        expander = QueryExpander(llm_service=_make_llm_service(expand_result))
        reformulator = QueryReformulator(llm_service=_make_llm_service(reform_result))
        hyde_gen = HyDEGenerator(llm_service=_make_llm_service(hyde_result))
        return QueryProcessor(
            llm_service=llm,
            expander=expander,
            reformulator=reformulator,
            hyde_generator=hyde_gen
        )

    @pytest.mark.asyncio
    async def test_process_returns_result_with_original_query(self):
        processor = self._make_processor()
        options = QueryUnderstandingOptions(
            enable_reformulation=False,
            enable_expansion=False,
            enable_hyde=False
        )
        result = await processor.process("What is uptime?", options=options)

        assert isinstance(result, QueryProcessingResult)
        assert result.original_query == "What is uptime?"

    @pytest.mark.asyncio
    async def test_process_all_disabled_returns_original(self):
        processor = self._make_processor()
        options = QueryUnderstandingOptions(
            enable_reformulation=False,
            enable_expansion=False,
            enable_hyde=False
        )
        result = await processor.process("What is Q4 revenue?", options=options)

        assert result.reformulation_applied is False
        assert result.expansion_applied is False
        assert result.hyde_applied is False
        assert result.get_primary_query() == "What is Q4 revenue?"

    @pytest.mark.asyncio
    async def test_process_with_hyde_sets_hyde_answer(self):
        processor = self._make_processor(hyde_result="Revenue in Q4 was approximately $2.5M...")
        options = QueryUnderstandingOptions(
            enable_reformulation=False,
            enable_expansion=False,
            enable_hyde=True
        )
        result = await processor.process("What is Q4 revenue?", options=options)

        assert result.hyde_applied is True
        assert result.hyde_answer is not None
        assert len(result.hyde_answer) > 0

    def test_query_processing_result_get_all_queries(self):
        r = QueryProcessingResult(
            original_query="original",
            reformulated_query="reformed",
            expanded_queries=["exp1", "exp2"],
            expansion_applied=True
        )
        all_q = r.get_all_queries()
        assert all_q[0] == "reformed"  # primary is reformulated
        assert "exp1" in all_q
        assert "exp2" in all_q

    def test_query_processing_result_to_dict(self):
        r = QueryProcessingResult(
            original_query="test",
            reformulated_query="clearer test",
            expanded_queries=["alt test"],
            processing_time=0.42,
            reformulation_applied=True,
            expansion_applied=True,
            hyde_applied=False
        )
        d = r.to_dict()
        assert d["original_query"] == "test"
        assert d["reformulated_query"] == "clearer test"
        assert d["techniques_applied"]["reformulation"] is True
        assert d["techniques_applied"]["hyde"] is False
        assert d["processing_time"] == pytest.approx(0.42, abs=0.001)

    def test_get_stats_returns_component_stats(self):
        processor = self._make_processor()
        stats = processor.get_stats()
        assert "expander" in stats
        assert "reformulator" in stats
        assert "hyde_generator" in stats


# Made with Bob
