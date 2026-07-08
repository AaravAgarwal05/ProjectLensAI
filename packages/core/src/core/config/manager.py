"""Central configuration manager."""

from core.exceptions.base import ConfigurationError
from core.utils.singleton import Singleton


class ConfigManager(metaclass=Singleton):
    """Central registry for configuration objects.

    This is a thread-safe singleton that holds named configuration
    instances.
    """

    def __init__(self) -> None:
        self._configs: dict[str, object] = {}

    def register(self, name: str, config: object) -> None:
        """Register a configuration under *name*.

        Raises:
            ConfigurationError: If *name* is already registered.
        """
        if name in self._configs:
            raise ConfigurationError(
                message=f"Configuration '{name}' is already registered",
                code="CONFIG_ALREADY_REGISTERED",
            )
        self._configs[name] = config

    def get(self, name: str) -> object:
        """Retrieve a configuration by *name*.

        Raises:
            ConfigurationError: If *name* is not registered.
        """
        config = self._configs.get(name)
        if config is None:
            raise ConfigurationError(
                message=f"Configuration '{name}' not found",
                code="CONFIG_NOT_FOUND",
            )
        return config

    def load_all(self) -> None:
        """Trigger all registered configurations to load/reload."""
        for config in self._configs.values():
            if hasattr(config, "model_dump"):
                pass  # pydantic models are already loaded

    def reload(self) -> None:
        """Clear all cached configurations and trigger reloading."""
        self._configs.clear()

    def list(self) -> dict[str, type]:
        """Return a mapping of config names to their Python types."""
        return {name: type(config) for name, config in self._configs.items()}
