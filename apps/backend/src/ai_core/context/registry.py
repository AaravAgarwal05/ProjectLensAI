"""Registry for context strategies with lazy instantiation."""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.context.base import ContextStrategy
from src.ai_core.context.exceptions import StrategyNotFoundError

logger = logging.getLogger(__name__)


class ContextRegistry:
    """Registry of context strategy classes (lazy instantiation)."""

    def __init__(self) -> None:
        self._strategies: dict[str, type[ContextStrategy]] = {}
        self._instances: dict[str, ContextStrategy] = {}

    def register(self, name: str, strategy_cls: type[ContextStrategy]) -> None:
        if name in self._strategies:
            logger.warning("Overwriting strategy '%s'", name)
        self._strategies[name] = strategy_cls
        self._instances.pop(name, None)
        logger.debug("Registered context strategy '%s'", name)

    def get(self, name: str) -> ContextStrategy:
        if name not in self._strategies:
            msg = f"Unknown context strategy: '{name}'"
            raise StrategyNotFoundError(msg)
        if name not in self._instances:
            self._instances[name] = self._strategies[name]()
        return self._instances[name]

    def unregister(self, name: str) -> bool:
        self._instances.pop(name, None)
        return self._strategies.pop(name, None) is not None

    def list_names(self) -> list[str]:
        return list(self._strategies.keys())

    def clear(self) -> None:
        self._strategies.clear()
        self._instances.clear()


class ContextFactory:
    """Factory for creating context strategies with alias support."""

    def __init__(self) -> None:
        self.registry = ContextRegistry()
        self._aliases: dict[str, str] = {}

    def set_alias(self, alias: str, target: str) -> None:
        self._aliases[alias] = target

    def resolve(self, name: str) -> str:
        return self._aliases.get(name, name)

    def create(self, name: str, params: dict[str, Any] | None = None) -> ContextStrategy:
        resolved = self.resolve(name)
        strategy = self.registry.get(resolved)
        if params:
            strategy.configure(params)
        return strategy
