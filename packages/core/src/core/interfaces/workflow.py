"""Workflow interface."""

from abc import ABC, abstractmethod


class IWorkflow(ABC):
    """Abstract interface for executable workflows."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the workflow name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the workflow version."""

    @abstractmethod
    def execute(self, context: dict) -> dict:
        """Execute the workflow with the given context and return results."""

    @abstractmethod
    def validate(self) -> bool:
        """Validate the workflow definition. Returns True if valid."""
