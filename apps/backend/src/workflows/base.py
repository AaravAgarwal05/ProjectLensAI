"""Abstract workflow interface and error recovery."""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseWorkflow(ABC):
    """Interface for application workflows.

    Workflows orchestrate multiple steps (retrieval, LLM calls,
    post-processing) and provide built-in rollback for error recovery.
    """

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run the workflow with the given context.

        Args:
            context: Input parameters and shared state for the workflow.

        Returns:
            The workflow result as a dictionary.
        """

    @abstractmethod
    def validate_input(self, data: dict[str, Any]) -> bool:
        """Validate that the input data is sufficient to execute.

        Args:
            data: The raw input data.

        Returns:
            True if input is valid, False otherwise.
        """

    async def rollback(self, context: dict[str, Any]) -> None:
        """Undo side effects after a failed execution.

        Subclasses should override this if they perform mutations that
        need reversal (e.g. cleaning up created records).

        Args:
            context: The workflow context at the point of failure.
        """
        logger.warning(
            "Rollback called for %s — no specialised recovery implemented",
            type(self).__name__,
        )
