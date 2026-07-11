"""Tests for MetadataEnricher."""

from src.ai_core.context.metadata import MetadataEnricher
from src.ai_core.context.models import ContextChunk


class TestMetadataEnricher:
    def test_empty_chunks(self):
        enricher = MetadataEnricher()
        assert enricher.enrich([], {}) == []

    def test_enrich_with_extra(self):
        enricher = MetadataEnricher()
        chunks = [ContextChunk(chunk_id="c1", content="test")]
        result = enricher.enrich(chunks, {"report_title": "My Report", "report_version": "2.1"})
        assert result[0].source_title == "My Report"
        assert result[0].source_version == "2.1"

    def test_enrich_preserves_existing(self):
        enricher = MetadataEnricher()
        chunks = [ContextChunk(chunk_id="c1", content="test", source_title="Existing")]
        result = enricher.enrich(chunks, {"report_title": "Override"})
        assert result[0].source_title == "Existing"  # not overridden

    def test_enrich_page_number(self):
        enricher = MetadataEnricher()
        chunks = [ContextChunk(chunk_id="c1", content="test")]
        result = enricher.enrich(chunks, {"page_number": 42})
        assert result[0].page_number == 42

    def test_enrich_section_name(self):
        enricher = MetadataEnricher()
        chunks = [ContextChunk(chunk_id="c1", content="test")]
        result = enricher.enrich(chunks, {"section_name": "Introduction"})
        assert result[0].section_name == "Introduction"

    def test_enrich_source_id_and_citation(self):
        enricher = MetadataEnricher()
        chunks = [ContextChunk(chunk_id="c1", content="test")]
        result = enricher.enrich(chunks, {"source_id": "src1"})
        assert result[0].source_id == "src1"
        assert "src1" in result[0].citations

    def test_enrich_extra_metadata(self):
        enricher = MetadataEnricher()
        chunks = [ContextChunk(chunk_id="c1", content="test")]
        result = enricher.enrich(chunks, {"custom_key": "custom_value"})
        assert result[0].metadata.get("custom_key") == "custom_value"
