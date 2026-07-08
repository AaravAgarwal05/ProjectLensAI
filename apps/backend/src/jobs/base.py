"""Base job interface for background task processing."""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseJob(ABC):
    """Interface for background jobs.

    Jobs encapsulate a unit of asynchronous work with lifecycle hooks
    for success and failure handling.
    """

    @abstractmethod
    async def run(self) -> Any:
        """Execute the job and return its result.

        Subclasses implement the actual business logic here.
        """

    async def on_success(self, result: Any) -> None:
        """Callback invoked after successful execution.

        Args:
            result: The value returned by ``run()``.
        """
        logger.info("Job %s completed successfully", type(self).__name__)

    async def on_failure(self, error: Exception) -> None:
        """Callback invoked when ``run()`` raises an exception.

        Args:
            error: The exception that was raised.
        """
        logger.error("Job %s failed: %s", type(self).__name__, error, exc_info=True)

    async def execute(self) -> Any:
        """Run the job with automatic success/failure callbacks.

        Returns:
            The job result on success.

        Raises:
            Exception: Re-raises any exception from ``run()`` after calling
                       ``on_failure``.
        """
        try:
            result = await self.run()
            await self.on_success(result)
            return result
        except Exception as exc:
            await self.on_failure(exc)
            raise
