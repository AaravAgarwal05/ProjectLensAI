"""Base exception hierarchy for ProjectLens."""


class ProjectLensError(Exception):
    """Base exception for all ProjectLens errors."""

    def __init__(self, message: str = "", code: str = "UNKNOWN") -> None:
        self.code = code
        super().__init__(message)


class ConfigurationError(ProjectLensError):
    """Raised when a configuration is invalid or missing."""

    def __init__(self, message: str = "", code: str = "CONFIG_ERROR") -> None:
        super().__init__(message, code)


class ProviderError(ProjectLensError):
    """Raised when a provider operation fails."""

    def __init__(self, message: str = "", code: str = "PROVIDER_ERROR") -> None:
        super().__init__(message, code)


class ValidationError(ProjectLensError):
    """Raised when data validation fails."""

    def __init__(self, message: str = "", code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message, code)
