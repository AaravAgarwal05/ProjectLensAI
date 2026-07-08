"""Fixtures for embedding tests."""

import pytest

from src.ai_core.chunking.models import Chunk


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    """Return sample Chunk objects for testing."""
    return [
        Chunk(text="Hello world, this is a test document."),
        Chunk(text="The second chunk has more content for embedding."),
        Chunk(text="Third chunk provides additional variety."),
        Chunk(text="Fourth chunk. More data here for batch testing."),
        Chunk(text="Fifth and final chunk for batch processing."),
    ]
