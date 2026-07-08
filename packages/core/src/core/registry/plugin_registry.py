"""Plugin registry — singleton that manages IPlugin instances."""

from __future__ import annotations

import threading

from core.exceptions.registry import (
    DuplicateRegistrationError,
    PluginNotFoundError,
)
from core.interfaces.plugin import IPlugin
from core.utils.singleton import Singleton


class PluginRegistry(metaclass=Singleton):
    """Thread-safe singleton registry for plugins."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._plugins: dict[str, IPlugin] = {}

    def register(self, name: str, plugin: IPlugin) -> None:
        """Register a plugin under *name*.

        Raises:
            DuplicateRegistrationError: If *name* is already registered.
        """
        with self._lock:
            if name in self._plugins:
                raise DuplicateRegistrationError(
                    message=f"Plugin '{name}' is already registered",
                    code="PLUGIN_ALREADY_REGISTERED",
                )
            self._plugins[name] = plugin

    def unregister(self, name: str) -> None:
        """Unregister a plugin by *name*.

        Raises:
            PluginNotFoundError: If *name* is not registered.
        """
        with self._lock:
            plugin = self._plugins.pop(name, None)
            if plugin is None:
                raise PluginNotFoundError(
                    message=f"Plugin '{name}' not found",
                    code="PLUGIN_NOT_FOUND",
                )
            plugin.unregister()

    def get(self, name: str) -> IPlugin:
        """Retrieve a plugin by *name*.

        Raises:
            PluginNotFoundError: If *name* is not registered.
        """
        with self._lock:
            plugin = self._plugins.get(name)
            if plugin is None:
                raise PluginNotFoundError(
                    message=f"Plugin '{name}' not found",
                    code="PLUGIN_NOT_FOUND",
                )
            return plugin

    def list(self) -> dict[str, IPlugin]:
        """Return all registered plugins as a name-to-plugin mapping."""
        with self._lock:
            return dict(self._plugins)

    def get_all(self) -> list[IPlugin]:
        """Return all registered plugins as a list."""
        with self._lock:
            return list(self._plugins.values())
