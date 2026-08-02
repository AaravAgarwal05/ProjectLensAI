"""Tests for embedding configuration."""

from src.ai_core.embedding.configuration import EmbeddingConfiguration


class TestEmbeddingConfiguration:
    def test_defaults(self):
        cfg = EmbeddingConfiguration()
        assert cfg.provider == "gemini"
        assert cfg.model_name == "BAAI/bge-small-en-v1.5"
        assert cfg.batch_size == 32
        assert cfg.device == "cpu"
        assert cfg.ollama_model == "nomic-embed-text"
        assert cfg.ollama_base_url == "http://localhost:11434"
        assert cfg.gemini_model == "text-embedding-004"

    def test_default_classmethod(self):
        cfg = EmbeddingConfiguration.default()
        assert cfg.provider == "gemini"

    def test_merge(self):
        cfg = EmbeddingConfiguration(batch_size=16)
        merged = cfg.merge({"batch_size": 64})
        assert merged.batch_size == 64
        assert merged.provider == "gemini"  # unchanged

    def test_merge_new_key(self):
        cfg = EmbeddingConfiguration()
        merged = cfg.merge({"extra": {"key": "val"}})
        assert merged.extra["key"] == "val"
