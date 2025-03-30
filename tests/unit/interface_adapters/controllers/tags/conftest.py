# tests/unit/interface_adapters/controllers/tags/conftest.py
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.repositories.tag_repository import TagRepository
from src.drivers.rest.schemas.tag_schemas import TagOperationRequest
from src.entities.models.tag import Tag
from tests.utils.entity_factories import create_tag


@pytest.fixture
def mock_tag_repository() -> AsyncMock:
    """Provides a mocked TagRepository for tag controller tests."""
    mock = AsyncMock(spec=TagRepository)
    mock.get_by_name = AsyncMock()
    return mock


@pytest.fixture
def sample_calibration_id() -> UUID:
    """Provides a consistent sample Calibration UUID."""
    # Use a specific UUID for predictability if required across tests
    return UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
def sample_tag_name() -> str:
    """Provides a consistent sample tag name."""
    return "shared-test-tag"


@pytest.fixture
def valid_request(sample_tag_name: str) -> TagOperationRequest:
    """Provides a valid TagOperationRequest based on sample_tag_name."""
    return TagOperationRequest(tag=sample_tag_name)


@pytest.fixture
def sample_tag(sample_tag_name: str) -> Tag:
    """Provides a sample Tag object using the factory."""
    # Use factory, override name, let factory handle ID by default
    return create_tag(name=sample_tag_name)
