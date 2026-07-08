"""Provider registry — singleton that manages BaseProvider subclasses."""

import threading
from typing import Any

from core.exceptions.base import ProviderError
from core.exceptions.registry import ProviderNotFoundError
from core.interfaces.provider import BaseProvider
from core.utils.singleton import Singleton


class ProviderRegistry(metaclass=Singleton):
    """Thread-safe singleton registry for provider classes.

    Providers are categorised (e.g. ``"llm"``, ``"embedding"``, ``"storage"``)
    and lazily instantiated with caching.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._classes: dict[str, dict[str, type[BaseProvider]]] = {}
        self._instances: dict[str, dict[str, BaseProvider]] = {}
        self._initialized: bool = False

    def register(self, category: str, name: str, provider_class: type) -> None:
        """Register a provider *class* under **category*/*name*.

        Args:
            category: Provider category (e.g. ``"llm"``).
            name: Provider name (e.g. ``"openai"``).
            provider_class: A subclass of :class:`BaseProvider`.
        """
        with self._lock:
            self._classes.setdefault(category, {})[name] = provider_class

    def get(self, category: str, name: str, **kwargs: Any) -> BaseProvider:
        """Get (or create and cache) a provider instance.

        The instance is created on first access with the supplied
        *kwargs* and cached for subsequent calls.

        Raises:
            ProviderNotFoundError: If the category/name combination is
                not registered.
        """
        with self._lock:
            cat_classes = self._classes.get(category, {})
            provider_cls = cat_classes.get(name)
            if provider_cls is None:
                raise ProviderNotFoundError(
                    message=f"Provider '{category}/{name}' not found",
                    code="PROVIDER_NOT_FOUND",
                )

            cat_instances = self._instances.setdefault(category, {})
            if name not in cat_instances:
                try:
                    instance = provider_cls(**kwargs)
                except Exception as exc:
                    raise ProviderError(
                        message=f"Failed to instantiate provider '{category}/{name}': {exc}",
                        code="PROVIDER_INSTANTIATION_ERROR",
                    ) from exc
                instance.initialize()
                cat_instances[name] = instance

            return cat_instances[name]

    def list(self, category: str | None = None) -> dict:
        """List registered providers, optionally filtered by *category*."""
        with self._lock:
            if category is not None:
                return dict(self._classes.get(category, {}))
            return {cat: dict(classes) for cat, classes in self._classes.items()}

    def clear(self) -> None:
        """Shut down and remove all cached instances and registrations."""
        with self._lock:
            for cat_instances in self._instances.values():
                for instance in cat_instances.values():
                    instance.shutdown()
            self._instances.clear()
            self._classes.clear()
