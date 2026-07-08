"""Plugin interface."""

from abc import ABC, abstractmethod


class IPlugin(ABC):
    """Abstract interface for pluggable extensions."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""

    @abstractmethod
    def register(self) -> None:
        """Register the plugin with the system."""

    @abstractmethod
    def unregister(self) -> None:
        """Unregister the plugin from the system."""

    @property
    def hooks(self) -> dict:
        """Return the hooks this plugin provides.

        Returns an empty dict by default.
        """
        return {}
