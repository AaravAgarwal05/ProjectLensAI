"""Tests for LLMRegistry and LLMFactory."""

import pytest

from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.exceptions import ProviderNotFoundError
from src.ai_core.llm.providers.ollama import OllamaProvider
from src.ai_core.llm.registry import LLMFactory, LLMRegistry


class TestLLMRegistry:
    def test_register_and_get(self):
        reg = LLMRegistry()
        reg.register("ollama", OllamaProvider)
        provider = reg.get("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_get_unknown(self):
        reg = LLMRegistry()
        with pytest.raises(ProviderNotFoundError):
            reg.get("nonexistent")

    def test_lazy_instantiation(self):
        reg = LLMRegistry()
        reg.register("ollama", OllamaProvider)
        p1 = reg.get("ollama")
        p2 = reg.get("ollama")
        assert p1 is p2  # same instance

    def test_unregister(self):
        reg = LLMRegistry()
        reg.register("ollama", OllamaProvider)
        reg.unregister("ollama")
        assert "ollama" not in reg.list_names()

    def test_list_names(self):
        reg = LLMRegistry()
        reg.register("ollama", OllamaProvider)
        assert reg.list_names() == ["ollama"]

    def test_clear(self):
        reg = LLMRegistry()
        reg.register("ollama", OllamaProvider)
        reg.get("ollama")
        reg.clear()
        assert reg.list_names() == []
        with pytest.raises(ProviderNotFoundError):
            reg.get("ollama")

    def test_register_overwrite_warning(self):
        reg = LLMRegistry()

        class FakeProvider1(OllamaProvider):
            @property
            def provider_name(self) -> str:
                return "fake1"

        class FakeProvider2(OllamaProvider):
            @property
            def provider_name(self) -> str:
                return "fake2"

        reg.register("test", FakeProvider1)
        reg.register("test", FakeProvider2)  # overwrite
        provider = reg.get("test")
        assert isinstance(provider, FakeProvider2)


class TestLLMFactory:
    def test_create(self):
        factory = LLMFactory()
        factory.registry.register("ollama", OllamaProvider)
        provider = factory.create("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_create_unknown(self):
        factory = LLMFactory()
        with pytest.raises(ProviderNotFoundError):
            factory.create("nonexistent")

    def test_create_with_config(self):
        factory = LLMFactory()
        factory.registry.register("ollama", OllamaProvider)
        config = LLMConfiguration(model_name="test:latest")
        provider = factory.create("ollama", config)
        assert provider._config.model_name == "test:latest"

    def test_alias_resolution(self):
        factory = LLMFactory()
        factory.registry.register("ollama", OllamaProvider)
        factory.set_alias("local", "ollama")
        provider = factory.create("local")
        assert isinstance(provider, OllamaProvider)

    def test_available_providers(self):
        factory = LLMFactory()
        factory.registry.register("ollama", OllamaProvider)
        factory.set_alias("local", "ollama")
        names = factory.available_providers()
        assert "ollama" in names
        assert "local" in names
