"""Registry-specific exceptions."""

from core.exceptions.base import ProjectLensError


class PluginNotFoundError(ProjectLensError):
    """Raised when a requested plugin is not registered."""

    def __init__(self, message: str = "", code: str = "PLUGIN_NOT_FOUND") -> None:
        super().__init__(message, code)


class DuplicateRegistrationError(ProjectLensError):
    """Raised when trying to register a duplicate item."""

    def __init__(self, message: str = "", code: str = "DUPLICATE_REGISTRATION") -> None:
        super().__init__(message, code)


class ProviderNotFoundError(ProjectLensError):
    """Raised when a requested provider is not registered."""

    def __init__(self, message: str = "", code: str = "PROVIDER_NOT_FOUND") -> None:
        super().__init__(message, code)
