"""Tests for context registry, factory, and configuration."""

import pytest

from src.ai_core.context.base import ContextStrategy
from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.exceptions import StrategyNotFoundError
from src.ai_core.context.models import LLMContext
from src.ai_core.context.registry import ContextFactory, ContextRegistry


class _FakeStrategy(ContextStrategy):
    @property
    def strategy_name(self) -> str:
        return "fake"

    async def assemble(self, query, chunks, history, config):
        return LLMContext(query=query)

    def configure(self, params: dict) -> None:
        pass


class TestContextRegistry:
    def test_register_and_get(self):
        reg = ContextRegistry()
        reg.register("fake", _FakeStrategy)
        s = reg.get("fake")
        assert s.strategy_name == "fake"

    def test_get_unknown(self):
        reg = ContextRegistry()
        with pytest.raises(StrategyNotFoundError):
            reg.get("nonexistent")

    def test_lazy_instantiation(self):
        reg = ContextRegistry()
        reg.register("fake", _FakeStrategy)
        s1 = reg.get("fake")
        s2 = reg.get("fake")
        assert s1 is s2

    def test_unregister(self):
        reg = ContextRegistry()
        reg.register("fake", _FakeStrategy)
        assert reg.unregister("fake") is True
        assert reg.unregister("fake") is False

    def test_list_names(self):
        reg = ContextRegistry()
        reg.register("a", _FakeStrategy)
        reg.register("b", _FakeStrategy)
        assert set(reg.list_names()) == {"a", "b"}

    def test_clear(self):
        reg = ContextRegistry()
        reg.register("fake", _FakeStrategy)
        reg.clear()
        assert reg.list_names() == []


class TestContextFactory:
    def test_create(self):
        factory = ContextFactory()
        factory.registry.register("fake", _FakeStrategy)
        s = factory.create("fake")
        assert isinstance(s, _FakeStrategy)

    def test_create_unknown(self):
        factory = ContextFactory()
        with pytest.raises(StrategyNotFoundError):
            factory.create("unknown")

    def test_create_with_aliases(self):
        factory = ContextFactory()
        factory.registry.register("real", _FakeStrategy)
        factory.set_alias("default", "real")
        s = factory.create("default")
        assert isinstance(s, _FakeStrategy)

    def test_available_strategies(self):
        factory = ContextFactory()
        factory.registry.register("a", _FakeStrategy)
        factory.registry.register("b", _FakeStrategy)
        names = factory.registry.list_names()
        assert "a" in names
        assert "b" in names


class TestContextConfiguration:
    def test_defaults(self):
        cfg = ContextConfiguration.default()
        assert cfg.max_tokens == 8192
        assert cfg.max_chunks == 20

    def test_merge(self):
        cfg = ContextConfiguration.default()
        merged = cfg.merge({"max_tokens": 4096})
        assert merged.max_tokens == 4096
        assert cfg.max_tokens == 8192  # unchanged

    def test_custom(self):
        cfg = ContextConfiguration(
            max_tokens=16384,
            max_chunks=50,
            system_prompt_tokens=1000,
        )
        assert cfg.max_tokens == 16384
        assert cfg.max_chunks == 50

    def test_to_dict(self):
        cfg = ContextConfiguration(max_tokens=4096)
        d = cfg.to_dict()
        assert d["max_tokens"] == 4096
        assert "max_chunks" in d
