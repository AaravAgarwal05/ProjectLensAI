"""Abstract text cleaner interface and composite pipeline."""

from abc import ABC, abstractmethod


class TextCleaner(ABC):
    """Abstract base class for stateless, thread-safe text cleaners."""

    @abstractmethod
    def clean(self, text: str) -> str:
        """Clean *text* and return the result."""

    @property  # type: ignore[misc]
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this cleaner."""


class CleaningPipeline:
    """Compose multiple ``TextCleaner`` instances and run them in sequence.

    Examples
    --------
    .. code-block:: python

        pipeline = CleaningPipeline([WhitespaceCleaner(), UnicodeCleaner()])
        result = pipeline.run(raw_text)
    """

    def __init__(self, cleaners: list[TextCleaner] | None = None) -> None:
        self._cleaners: list[TextCleaner] = list(cleaners) if cleaners else []

    def add_cleaner(self, cleaner: TextCleaner) -> None:
        """Append *cleaner* to the pipeline."""
        self._cleaners.append(cleaner)

    def run(self, text: str) -> str:
        """Apply every registered cleaner in sequence."""
        for cleaner in self._cleaners:
            text = cleaner.clean(text)
        return text

    @property
    def cleaners(self) -> list[TextCleaner]:
        """Return a copy of the internal cleaner list."""
        return list(self._cleaners)

    def __repr__(self) -> str:
        names = [c.name for c in self._cleaners]
        return f"CleaningPipeline([{', '.join(names)}])"
