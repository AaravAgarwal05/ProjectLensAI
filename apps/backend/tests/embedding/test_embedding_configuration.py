"""Tests for embedding configuration."""

from src.ai_core.embedding.configuration import EmbeddingConfiguration


class TestEmbeddingConfiguration:
    def test_defaults(self):
        cfg = EmbeddingConfiguration()
        assert cfg.provider == "sentence_transformers"
        assert cfg.model_name == "BAAI/bge-small-en-v1.5"
        assert cfg.batch_size == 32
        assert cfg.device == "cpu"
        assert cfg.ollama_model == "nomic-embed-text"
        assert cfg.ollama_base_url == "http://localhost:11434"

    def test_default_classmethod(self):
        cfg = EmbeddingConfiguration.default()
        assert cfg.provider == "sentence_transformers"

    def test_merge(self):
        cfg = EmbeddingConfiguration(batch_size=16)
        merged = cfg.merge({"batch_size": 64})
        assert merged.batch_size == 64
        assert merged.provider == "sentence_transformers"  # unchanged

    def test_merge_new_key(self):
        cfg = EmbeddingConfiguration()
        merged = cfg.merge({"extra": {"key": "val"}})
        assert merged.extra["key"] == "val"
