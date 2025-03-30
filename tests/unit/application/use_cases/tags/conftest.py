from unittest.mock import AsyncMock

import pytest

from src.application.repositories.tag_repository import TagRepository


@pytest.fixture
def mock_tag_repository() -> AsyncMock:
    """Fixture for a mocked TagRepository, shared across tag use case tests."""
    return AsyncMock(spec=TagRepository)
