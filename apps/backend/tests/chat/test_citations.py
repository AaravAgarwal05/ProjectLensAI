"""Tests for CitationEngine."""

from __future__ import annotations

from src.ai_core.chat.citations import CitationEngine
from src.ai_core.chat.models import CitationReference
from src.ai_core.context.models import ContextChunk


class TestCitationEngine:
    def test_extract_empty_chunks(self):
        engine = CitationEngine()
        result = engine.extract([], "response text")
        assert result == []

    def test_extract_no_matches_in_response(self):
        engine = CitationEngine(max_citations=5)
        chunks = [
            ContextChunk(
                chunk_id="c1",
                content="Some content about ML.",
                score=0.95,
                source_id="r1",
                source_title="Report 1",
                page_number=5,
                section_name="Methodology",
            )
        ]
        result = engine.extract(chunks, "Response without citation markers")
        assert len(result) == 1
        assert result[0].chunk_id == "c1"
        assert result[0].report_id == "r1"

    def test_extract_with_citation_markers(self):
        engine = CitationEngine(max_citations=5)
        chunks = [
            ContextChunk(
                chunk_id="c1",
                content="Random forest algorithm achieves 94% accuracy.",
                score=0.95,
                source_id="r1",
                source_title="Report 1",
                page_number=5,
                section_name="Results",
            )
        ]
        response = "The model uses random forest algorithm [src_c1] and achieves 94% accuracy."
        result = engine.extract(chunks, response)
        assert len(result) >= 1
        assert result[0].chunk_id == "c1"

    def test_extract_deduplicates_by_chunk_id(self):
        engine = CitationEngine(max_citations=5)
        chunks = [
            ContextChunk(
                chunk_id="c1",
                content="Content A",
                score=0.95,
                source_id="r1",
                source_title="R1",
                page_number=1,
                section_name="S1",
            ),
            ContextChunk(
                chunk_id="c1",
                content="Content A (duplicate)",
                score=0.90,
                source_id="r1",
                source_title="R1",
                page_number=1,
                section_name="S1",
            ),
        ]
        result = engine.extract(chunks, "Some text [src_c1]")
        ids = [c.chunk_id for c in result]
        assert len([i for i in ids if i == "c1"]) <= 1

    def test_extract_respects_max_citations(self):
        engine = CitationEngine(max_citations=2)
        chunks = [
            ContextChunk(
                chunk_id=f"c{i}",
                content=f"Content {i}",
                score=1.0 - (i * 0.1),
                source_id=f"r{i}",
                source_title=f"R{i}",
                page_number=i,
                section_name=f"S{i}",
            )
            for i in range(5)
        ]
        result = engine.extract(chunks, "Response text.")
        assert len(result) <= 2

    def test_extract_ranks_by_score(self):
        engine = CitationEngine(max_citations=10)
        chunks = [
            ContextChunk(
                chunk_id=f"c{i}",
                content=f"Content {i}",
                score=float(i),
                source_id=f"r{i}",
                source_title=f"R{i}",
                page_number=i,
                section_name=f"S{i}",
            )
            for i in range(3)
        ]
        result = engine.extract(chunks, "Response text.")
        scores = [c.score for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_to_dicts(self):
        engine = CitationEngine()
        citations = [
            CitationReference(
                report_id="r1",
                report_title="R1",
                page_number=5,
                section_name="S1",
                chunk_id="c1",
                score=0.95,
            )
        ]
        dicts = engine.to_dicts(citations)
        assert len(dicts) == 1
        assert dicts[0]["report_id"] == "r1"
        assert dicts[0]["score"] == 0.95

    def test_from_dicts(self):
        engine = CitationEngine()
        dicts = [
            {
                "report_id": "r1",
                "report_title": "R1",
                "page_number": 5,
                "section_name": "S1",
                "chunk_id": "c1",
                "score": 0.95,
            }
        ]
        citations = engine.from_dicts(dicts)
        assert len(citations) == 1
        assert citations[0].report_id == "r1"
        assert citations[0].score == 0.95

    def test_from_dicts_handles_missing_fields(self):
        engine = CitationEngine()
        dicts = [{"report_id": "r1"}]
        citations = engine.from_dicts(dicts)
        assert len(citations) == 1
        assert citations[0].report_id == "r1"
        assert citations[0].score == 0.0

    def test_round_trip(self):
        engine = CitationEngine()
        original = [
            CitationReference(
                report_id="r1",
                report_title="R1",
                page_number=5,
                section_name="S1",
                chunk_id="c1",
                score=0.95,
            )
        ]
        dicts = engine.to_dicts(original)
        restored = engine.from_dicts(dicts)
        assert len(restored) == len(original)
        assert restored[0].report_id == original[0].report_id
        assert restored[0].score == original[0].score
