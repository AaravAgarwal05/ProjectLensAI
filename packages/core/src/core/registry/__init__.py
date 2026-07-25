"""Registries package."""

from core.registry.factory import Factory
from core.registry.plugin_registry import PluginRegistry
from core.registry.provider_registry import ProviderRegistry

__all__ = [
    "PluginRegistry",
    "ProviderRegistry",
    "Factory",
]
