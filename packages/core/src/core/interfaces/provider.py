"""Base provider interface."""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for all providers.

    Providers are pluggable components that wrap external services,
    APIs, or data sources.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the provider version."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider, acquiring any resources needed."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shut down the provider, releasing all resources."""

    def health_check(self) -> bool:
        """Check whether the provider is healthy.

        Returns True by default; subclasses may override to add
        actual health-check logic.
        """
        return True
