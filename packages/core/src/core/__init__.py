"""ProjectLens Core - foundational package."""

from core.interfaces.provider import BaseProvider
from core.interfaces.repository import BaseRepository
from core.registry.plugin_registry import PluginRegistry
from core.registry.provider_registry import ProviderRegistry
from core.registry.factory import Factory
from core.events.bus import EventBus
from core.config.manager import ConfigManager
from core.exceptions.base import ProjectLensError
from core.logging.logger import get_logger, LoggerMixin
from core.utils.singleton import Singleton

__all__ = [
    "BaseProvider",
    "BaseRepository",
    "PluginRegistry",
    "ProviderRegistry",
    "Factory",
    "EventBus",
    "ConfigManager",
    "ProjectLensError",
    "get_logger",
    "LoggerMixin",
    "Singleton",
]
