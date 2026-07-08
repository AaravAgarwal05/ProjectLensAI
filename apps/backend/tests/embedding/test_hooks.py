"""Tests for EmbeddingHookRegistry."""

from src.ai_core.chunking.models import Chunk
from src.ai_core.embedding.hooks import EmbeddingHookEvent, EmbeddingHookRegistry


class TestEmbeddingHookRegistry:
    def test_register_and_run_before_embedding(self):
        registry = EmbeddingHookRegistry()
        calls = []

        def hook(chunks):
            calls.append("called")
            return chunks

        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, hook, name="h1")
        result = registry.run_before_embedding([Chunk(text="test")])
        assert len(calls) == 1
        assert len(result) == 1

    def test_multiple_hooks_order(self):
        registry = EmbeddingHookRegistry()
        order = []

        def h1(chunks):
            order.append(1)
            return chunks

        def h2(chunks):
            order.append(2)
            return chunks

        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, h1, name="h1")
        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, h2, name="h2")
        registry.run_before_embedding([Chunk(text="test")])
        assert order == [1, 2]

    def test_hook_modifies_chunks(self):
        registry = EmbeddingHookRegistry()

        def add_prefix(chunks):
            # Can't mutate frozen Chunk — create new
            chunks = [Chunk(text="prefix_" + c.text, chunk_id=c.chunk_id) for c in chunks]
            return chunks

        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, add_prefix, name="prefix")
        chunks = [Chunk(text="original")]
        result = registry.run_before_embedding(chunks)
        assert result[0].text == "prefix_original"

    def test_one_shot_hook(self):
        registry = EmbeddingHookRegistry()
        calls = []

        def hook(chunks):
            calls.append("called")
            return chunks

        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, hook, once=True, name="once")
        registry.run_before_embedding([Chunk(text="a")])
        registry.run_before_embedding([Chunk(text="b")])
        assert len(calls) == 1

    def test_unregister(self):
        registry = EmbeddingHookRegistry()

        def hook(chunks):
            return chunks

        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, hook, name="rm")
        assert registry.unregister("rm") is True
        assert registry.unregister("rm") is False

    def test_list_hooks(self):
        registry = EmbeddingHookRegistry()

        def hook(chunks):
            return chunks

        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, hook, name="h1")
        registry.register(EmbeddingHookEvent.AFTER_EMBEDDING, hook, name="h2")
        assert len(registry.list_hooks()) == 2
        assert len(registry.list_hooks(EmbeddingHookEvent.BEFORE_EMBEDDING)) == 1

    def test_clear(self):
        registry = EmbeddingHookRegistry()

        def hook(chunks):
            return chunks

        registry.register(EmbeddingHookEvent.BEFORE_EMBEDDING, hook, name="h1")
        registry.clear()
        assert len(registry.list_hooks()) == 0

    def test_after_batch_hook(self):
        registry = EmbeddingHookRegistry()
        calls = []

        def hook(chunks_and_embs):
            """after_batch hooks receive (chunks, embeddings) tuple."""
            calls.append("called")
            return chunks_and_embs[1]  # return embeddings

        registry.register(EmbeddingHookEvent.AFTER_BATCH, hook, name="ab")
        registry.run_after_batch([Chunk(text="t")], [])
        assert len(calls) == 1
