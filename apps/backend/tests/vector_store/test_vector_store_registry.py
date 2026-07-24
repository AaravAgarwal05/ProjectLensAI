"""Tests for vector-store registry and factory."""

import pytest

from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.configuration import VectorStoreConfiguration
from src.ai_core.vector_store.exceptions import StoreNotFoundError
from src.ai_core.vector_store.factory import VectorStoreFactory
from src.ai_core.vector_store.models import DeleteResult
from src.ai_core.vector_store.registry import VectorStoreRegistry


class _FakeStore(VectorStore):
    """Minimal fake store for registry testing."""

    @property
    def store_name(self) -> str:
        return "fake"

    async def health_check(self) -> bool:
        return True

    async def create_collection(self, name: str, **kwargs) -> bool:
        return True

    async def delete_collection(self, name: str) -> bool:
        return True

    async def collection_exists(self, name: str) -> bool:
        return True

    async def list_collections(self) -> list[str]:
        return ["test"]

    async def insert(self, collection: str, documents: list) -> int:
        return len(documents)

    async def update(self, collection: str, documents: list) -> int:
        return len(documents)

    async def delete(self, collection: str, chunk_ids=None, filter=None) -> int:
        return len(chunk_ids) if chunk_ids else 0

    async def count(self, collection: str) -> int:
        return 0

    async def delete_by_report(self, collection: str, report_id: str) -> "DeleteResult":
        return DeleteResult(collection_name=collection, deleted_count=0)

    async def delete_by_version(self, collection: str, version_id: str) -> "DeleteResult":
        return DeleteResult(collection_name=collection, deleted_count=0)

    def configure(self, params: dict) -> None:
        pass


class TestVectorStoreRegistry:
    def test_register_and_get(self):
        reg = VectorStoreRegistry()
        reg.register("fake", _FakeStore)
        store = reg.get("fake")
        assert store.store_name == "fake"

    def test_get_unknown(self):
        reg = VectorStoreRegistry()
        with pytest.raises(StoreNotFoundError):
            reg.get("nonexistent")

    def test_lazy_instantiation(self):
        reg = VectorStoreRegistry()
        reg.register("fake", _FakeStore)
        s1 = reg.get("fake")
        s2 = reg.get("fake")
        assert s1 is s2

    def test_unregister(self):
        reg = VectorStoreRegistry()
        reg.register("fake", _FakeStore)
        reg.unregister("fake")
        assert "fake" not in reg.list_names()

    def test_double_register(self):
        reg = VectorStoreRegistry()
        reg.register("fake", _FakeStore)
        with pytest.raises(ValueError):
            reg.register("fake", _FakeStore)


class TestVectorStoreFactory:
    def test_create(self):
        factory = VectorStoreFactory()
        factory.registry.register("fake", _FakeStore)
        store = factory.create("fake")
        assert isinstance(store, _FakeStore)

    def test_create_unknown(self):
        factory = VectorStoreFactory()
        with pytest.raises(StoreNotFoundError):
            factory.create("unknown")

    def test_create_with_aliases(self):
        factory = VectorStoreFactory()
        factory.registry.register("chroma", _FakeStore)
        store = factory.create("default")
        assert isinstance(store, _FakeStore)

    def test_available_stores(self):
        factory = VectorStoreFactory()
        factory.registry.register("a", _FakeStore)
        factory.registry.register("b", _FakeStore)
        stores = factory.available_stores()
        assert "a" in stores
        assert "b" in stores


class TestVectorStoreConfiguration:
    def test_defaults(self):
        cfg = VectorStoreConfiguration.default()
        assert cfg.store == "chroma"
        assert cfg.collection_name == "default"
        assert cfg.batch_size == 100

    def test_merge(self):
        cfg = VectorStoreConfiguration.default()
        merged = cfg.merge({"batch_size": 50})
        assert merged.batch_size == 50
        assert merged.store == "chroma"

    def test_custom(self):
        cfg = VectorStoreConfiguration(
            store="pgvector",
            collection_name="docs",
            batch_size=50,
            pgvector_dsn="postgres://localhost:5432/db",
        )
        assert cfg.store == "pgvector"
        assert cfg.pgvector_dsn == "postgres://localhost:5432/db"
