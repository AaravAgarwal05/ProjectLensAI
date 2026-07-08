"""Base service interface."""

from abc import ABC, abstractmethod


class BaseService(ABC):
    """Abstract base class for domain services."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the service name."""

    @abstractmethod
    def execute(self, **kwargs: dict) -> object:
        """Execute the service with the given keyword arguments."""

    @abstractmethod
    def validate(self, data: object) -> bool:
        """Validate input data. Returns True if valid."""
