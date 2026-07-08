"""Tests for the core package."""

from abc import ABC
from typing import Any

import pytest
from pydantic import BaseModel

from core import (
    BaseProvider,
    BaseRepository,
    ConfigManager,
    EventBus,
    Factory,
    PluginRegistry,
    ProjectLensError,
)
from core.config.base import BaseConfig
from core.config.env import EnvLoader
from core.events.types import Event
from core.exceptions.base import ConfigurationError, ProviderError, ValidationError
from core.exceptions.registry import (
    DuplicateRegistrationError,
    PluginNotFoundError,
    ProviderNotFoundError,
)
from core.exceptions.workflow import WorkflowError, WorkflowTimeoutError, WorkflowValidationError
from core.interfaces.plugin import IPlugin
from core.interfaces.service import BaseService
from core.interfaces.workflow import IWorkflow
from core.logging.config import LoggingConfig
from core.logging.logger import LoggerMixin, get_logger
from core.registry.provider_registry import ProviderRegistry
from core.utils.helpers import camel_to_snake, deep_merge, now_iso, snake_to_camel, truncate
from core.utils.singleton import Singleton


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_base_exception(self) -> None:
        err = ProjectLensError("oops", "ERR_01")
        assert str(err) == "oops"
        assert err.code == "ERR_01"

    def test_configuration_error(self) -> None:
        err = ConfigurationError("bad config")
        assert err.code == "CONFIG_ERROR"

    def test_provider_error(self) -> None:
        err = ProviderError("provider failed")
        assert err.code == "PROVIDER_ERROR"

    def test_validation_error(self) -> None:
        err = ValidationError("invalid")
        assert err.code == "VALIDATION_ERROR"

    def test_plugin_not_found(self) -> None:
        err = PluginNotFoundError("missing")
        assert err.code == "PLUGIN_NOT_FOUND"

    def test_duplicate_registration(self) -> None:
        err = DuplicateRegistrationError("dup")
        assert err.code == "DUPLICATE_REGISTRATION"

    def test_provider_not_found(self) -> None:
        err = ProviderNotFoundError("nope")
        assert err.code == "PROVIDER_NOT_FOUND"

    def test_workflow_error(self) -> None:
        err = WorkflowError("wf failed")
        assert err.code == "WORKFLOW_ERROR"

    def test_workflow_timeout(self) -> None:
        err = WorkflowTimeoutError("wf timed out")
        assert err.code == "WORKFLOW_TIMEOUT"

    def test_workflow_validation(self) -> None:
        err = WorkflowValidationError("wf invalid")
        assert err.code == "WORKFLOW_VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class _MySingleton(metaclass=Singleton):
    def __init__(self) -> None:
        self.value = 0


class TestSingleton:
    def test_same_instance(self) -> None:
        a = _MySingleton()
        b = _MySingleton()
        assert a is b

    def test_state_persists(self) -> None:
        a = _MySingleton()
        a.value = 42
        b = _MySingleton()
        assert b.value == 42


# ---------------------------------------------------------------------------
# PluginRegistry
# ---------------------------------------------------------------------------


class _FakePlugin(IPlugin):
    def __init__(self, name: str = "test-plugin") -> None:
        self._name = name
        self.registered = False
        self.unregistered = False

    @property
    def name(self) -> str:
        return self._name

    def register(self) -> None:
        self.registered = True

    def unregister(self) -> None:
        self.unregistered = True

    @property
    def hooks(self) -> dict:
        return {"on_start": lambda: None}


class TestPluginRegistry:
    def _reset(self) -> None:
        # Fresh instance for each test (Singleton caveat — use class-level reset)
        PluginRegistry._instances.pop(PluginRegistry, None)

    def test_register_and_get(self) -> None:
        PluginRegistry._instances.pop(PluginRegistry, None)
        registry = PluginRegistry()
        plugin = _FakePlugin()
        registry.register("test", plugin)
        assert registry.get("test") is plugin

    def test_duplicate_raises(self) -> None:
        PluginRegistry._instances.pop(PluginRegistry, None)
        registry = PluginRegistry()
        registry.register("dup", _FakePlugin())
        with pytest.raises(DuplicateRegistrationError):
            registry.register("dup", _FakePlugin())

    def test_unregister_removes(self) -> None:
        PluginRegistry._instances.pop(PluginRegistry, None)
        registry = PluginRegistry()
        plugin = _FakePlugin()
        registry.register("gone", plugin)
        registry.unregister("gone")
        assert plugin.unregistered
        with pytest.raises(PluginNotFoundError):
            registry.get("gone")

    def test_unregister_missing_raises(self) -> None:
        PluginRegistry._instances.pop(PluginRegistry, None)
        registry = PluginRegistry()
        with pytest.raises(PluginNotFoundError):
            registry.unregister("nope")

    def test_list_and_get_all(self) -> None:
        PluginRegistry._instances.pop(PluginRegistry, None)
        registry = PluginRegistry()
        p1 = _FakePlugin("a")
        p2 = _FakePlugin("b")
        registry.register("a", p1)
        registry.register("b", p2)
        assert set(registry.list().keys()) == {"a", "b"}
        assert set(registry.get_all()) == {p1, p2}


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class TestEventBus:
    def _reset(self) -> None:
        EventBus._instances.pop(EventBus, None)

    def test_publish_calls_handler(self) -> None:
        EventBus._instances.pop(EventBus, None)
        bus = EventBus()
        received: list[Event] = []

        def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("test.event", handler)
        event = Event(name="test.event", data={"key": "value"})
        bus.publish(event)
        assert len(received) == 1
        assert received[0].data == {"key": "value"}

    def test_unsubscribe(self) -> None:
        EventBus._instances.pop(EventBus, None)
        bus = EventBus()
        received: list[Event] = []

        def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        bus.publish(Event(name="test.event"))
        assert len(received) == 0

    def test_clear(self) -> None:
        EventBus._instances.pop(EventBus, None)
        bus = EventBus()

        def handler(event: Event) -> None:
            pass

        bus.subscribe("a", handler)
        bus.subscribe("b", handler)
        bus.clear()
        bus.publish(Event(name="a"))
        # No crash — handlers list is empty

    def test_event_defaults(self) -> None:
        event = Event(name="test")
        assert event.data == {}
        assert event.source == ""
        assert event.timestamp is not None


# ---------------------------------------------------------------------------
# ConfigManager
# ---------------------------------------------------------------------------


class TestConfigManager:
    def _reset(self) -> None:
        ConfigManager._instances.pop(ConfigManager, None)

    def test_register_and_get(self) -> None:
        ConfigManager._instances.pop(ConfigManager, None)
        mgr = ConfigManager()
        cfg = BaseConfig()
        mgr.register("main", cfg)
        assert mgr.get("main") is cfg

    def test_duplicate_raises(self) -> None:
        ConfigManager._instances.pop(ConfigManager, None)
        mgr = ConfigManager()
        mgr.register("dup", BaseConfig())
        with pytest.raises(ConfigurationError):
            mgr.register("dup", BaseConfig())

    def test_get_missing_raises(self) -> None:
        ConfigManager._instances.pop(ConfigManager, None)
        mgr = ConfigManager()
        with pytest.raises(ConfigurationError):
            mgr.get("nope")

    def test_list(self) -> None:
        ConfigManager._instances.pop(ConfigManager, None)
        mgr = ConfigManager()
        cfg = BaseConfig()
        mgr.register("main", cfg)
        listing = mgr.list()
        assert listing["main"] is BaseConfig


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestFactory:
    def test_register_and_create(self) -> None:
        factory = Factory()
        factory.register("int", lambda: 42)
        assert factory.create("int") == 42

    def test_create_with_kwargs(self) -> None:
        factory = Factory()
        factory.register("add", lambda a, b: a + b)
        assert factory.create("add", a=1, b=2) == 3

    def test_missing_key_raises(self) -> None:
        factory = Factory()
        with pytest.raises(KeyError):
            factory.create("nope")

    def test_keys(self) -> None:
        factory = Factory()
        factory.register("a", lambda: 1)
        factory.register("b", lambda: 2)
        assert sorted(factory.keys()) == ["a", "b"]

    def test_unregister(self) -> None:
        factory = Factory()
        factory.register("x", lambda: 1)
        factory.unregister("x")
        assert factory.keys() == []


# ---------------------------------------------------------------------------
# BaseProvider subclass
# ---------------------------------------------------------------------------


class _ConcreteProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "test-provider"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False


class TestBaseProvider:
    def test_create_and_health_check(self) -> None:
        provider = _ConcreteProvider()
        assert provider.name == "test-provider"
        assert provider.version == "1.0.0"
        assert provider.health_check() is True

    def test_initialize_and_shutdown(self) -> None:
        provider = _ConcreteProvider()
        provider.initialize()
        assert provider.initialized
        provider.shutdown()
        assert not provider.initialized


# ---------------------------------------------------------------------------
# ProviderRegistry
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    def _reset(self) -> None:
        ProviderRegistry._instances.pop(ProviderRegistry, None)

    def test_register_and_get(self) -> None:
        ProviderRegistry._instances.pop(ProviderRegistry, None)
        registry = ProviderRegistry()
        registry.register("llm", "test", _ConcreteProvider)
        provider = registry.get("llm", "test")
        assert isinstance(provider, _ConcreteProvider)

    def test_caches_instances(self) -> None:
        ProviderRegistry._instances.pop(ProviderRegistry, None)
        registry = ProviderRegistry()
        registry.register("llm", "cached", _ConcreteProvider)
        a = registry.get("llm", "cached")
        b = registry.get("llm", "cached")
        assert a is b

    def test_missing_raises(self) -> None:
        ProviderRegistry._instances.pop(ProviderRegistry, None)
        registry = ProviderRegistry()
        with pytest.raises(ProviderNotFoundError):
            registry.get("nope", "nope")

    def test_clear_shuts_down(self) -> None:
        ProviderRegistry._instances.pop(ProviderRegistry, None)
        registry = ProviderRegistry()
        registry.register("llm", "cleanup", _ConcreteProvider)
        provider = registry.get("llm", "cleanup")
        registry.clear()
        assert not provider.initialized

    def test_list(self) -> None:
        ProviderRegistry._instances.pop(ProviderRegistry, None)
        registry = ProviderRegistry()
        registry.register("llm", "a", _ConcreteProvider)
        registry.register("embedding", "b", _ConcreteProvider)
        listing = registry.list()
        assert "llm" in listing
        assert "embedding" in listing


# ---------------------------------------------------------------------------
# BaseRepository (interface-only test — generic)
# ---------------------------------------------------------------------------


class _Item(BaseModel):
    id: str
    value: int


class _ConcreteRepository(BaseRepository[_Item]):
    def __init__(self) -> None:
        self._items: dict[str, _Item] = {}

    def get(self, id: str) -> _Item | None:
        return self._items.get(id)

    def list(self, offset: int = 0, limit: int = 100) -> list[_Item]:
        return list(self._items.values())[offset : offset + limit]

    def create(self, data: _Item) -> _Item:
        self._items[data.id] = data
        return data

    def update(self, id: str, data: _Item) -> _Item:
        self._items[id] = data
        return data

    def delete(self, id: str) -> bool:
        return self._items.pop(id, None) is not None


class TestBaseRepository:
    def test_crud(self) -> None:
        repo = _ConcreteRepository()
        item = _Item(id="1", value=10)
        assert repo.create(item) is item
        assert repo.get("1") is item
        assert repo.list() == [item]
        updated = _Item(id="1", value=20)
        assert repo.update("1", updated).value == 20
        assert repo.delete("1") is True
        assert repo.get("1") is None

    def test_delete_missing(self) -> None:
        repo = _ConcreteRepository()
        assert repo.delete("nope") is False


# ---------------------------------------------------------------------------
# BaseService (interface-only)
# ---------------------------------------------------------------------------


class _ConcreteService(BaseService):
    @property
    def name(self) -> str:
        return "test-service"

    def execute(self, **kwargs: Any) -> object:
        return kwargs.get("input", "executed")

    def validate(self, data: Any) -> bool:
        return data is not None


class TestBaseService:
    def test_execute_and_validate(self) -> None:
        svc = _ConcreteService()
        assert svc.name == "test-service"
        assert svc.execute(input="hello") == "hello"
        assert svc.validate("x") is True
        assert svc.validate(None) is False


# ---------------------------------------------------------------------------
# IPlugin (hooks default)
# ---------------------------------------------------------------------------


class _MinimalPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "minimal"

    def register(self) -> None:
        pass

    def unregister(self) -> None:
        pass


class TestIPlugin:
    def test_hooks_default(self) -> None:
        plugin = _MinimalPlugin()
        assert plugin.hooks == {}

    def test_name(self) -> None:
        plugin = _MinimalPlugin()
        assert plugin.name == "minimal"


# ---------------------------------------------------------------------------
# IWorkflow (interface-only)
# ---------------------------------------------------------------------------


class _ConcreteWorkflow(IWorkflow):
    @property
    def name(self) -> str:
        return "test-wf"

    @property
    def version(self) -> str:
        return "2.0.0"

    def execute(self, context: dict) -> dict:
        return {"result": context.get("x", 0) * 2}

    def validate(self) -> bool:
        return True


class TestIWorkflow:
    def test_execute_and_validate(self) -> None:
        wf = _ConcreteWorkflow()
        assert wf.name == "test-wf"
        assert wf.version == "2.0.0"
        assert wf.execute({"x": 21}) == {"result": 42}
        assert wf.validate() is True


# ---------------------------------------------------------------------------
# BaseConfig
# ---------------------------------------------------------------------------


class TestBaseConfig:
    def test_to_dict(self) -> None:
        cfg = BaseConfig()
        d = cfg.to_dict()
        assert isinstance(d, dict)

    def test_merge(self) -> None:
        class SubConfig(BaseConfig):
            value: int = 1

        cfg = SubConfig()
        merged = cfg.merge({"value": 2})
        assert merged.value == 2
        assert cfg.value == 1  # original unchanged


# ---------------------------------------------------------------------------
# EnvLoader
# ---------------------------------------------------------------------------


class TestEnvLoader:
    def test_get_default(self) -> None:
        loader = EnvLoader()
        assert loader.get("NONEXISTENT", "fallback") == "fallback"

    def test_load_and_get(self) -> None:
        loader = EnvLoader()
        loader._vars = {"FOO": "bar"}
        assert loader.get("FOO") == "bar"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


class TestLogging:
    def test_logging_config_defaults(self) -> None:
        cfg = LoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.output == "console"

    def test_get_logger(self) -> None:
        logger = get_logger("test_logger")
        assert logger.name == "test_logger"
        assert logger.level == 20  # INFO

    def test_logger_mixin(self) -> None:
        class MyClass(LoggerMixin):
            pass

        obj = MyClass()
        assert obj.logger.name == "tests.test_core"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_snake_to_camel(self) -> None:
        assert snake_to_camel("hello_world") == "helloWorld"
        assert snake_to_camel("alreadyCamel") == "alreadyCamel"
        assert snake_to_camel("a") == "a"

    def test_camel_to_snake(self) -> None:
        assert camel_to_snake("helloWorld") == "hello_world"
        assert camel_to_snake("already_snake") == "already_snake"

    def test_truncate(self) -> None:
        assert truncate("hello world", 100) == "hello world"
        assert truncate("hello world", 8) == "hello..."

    def test_now_iso(self) -> None:
        iso = now_iso()
        assert "T" in iso

    def test_deep_merge(self) -> None:
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 99}, "e": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": {"c": 99, "d": 3}, "e": 4}
