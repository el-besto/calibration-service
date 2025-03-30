from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.repositories.tag_repository import TagRepository
from src.entities.models.tag import (
    Tag,  # Needed for mock_tag_repository side_effect hint
)
from tests.utils.entity_factories import (
    create_tag,  # Needed for mock_tag_repository side_effect
)

try:
    from datetime import UTC
except ImportError:
    from datetime import UTC


@pytest.fixture
def sample_calibration_id() -> UUID:
    """Provides a sample UUID for a calibration."""
    return uuid4()


@pytest.fixture
def sample_tag_id() -> UUID:
    """Provides a sample UUID for a tag."""
    return uuid4()


@pytest.fixture
def sample_timestamp() -> datetime:
    """Provides a sample datetime object (timezone-aware)."""
    return datetime.now(UTC)


@pytest.fixture
def mock_calibration_repository() -> AsyncMock:
    """Provides a base mocked CalibrationRepository. Specific methods should be mocked in tests."""
    mock = AsyncMock(spec=CalibrationRepository)
    # Add common mocks if needed, but usually better to mock specific methods per test/fixture
    mock.get = AsyncMock()
    mock.get_by_id = AsyncMock()  # Added get_by_id as it's commonly used
    mock.get_tag_associations_for_calibration = AsyncMock()
    mock.add_tags = AsyncMock(return_value=True)
    mock.add_tag_association = AsyncMock()  # Added as it's used in tests
    mock.update_tag_association = AsyncMock()
    mock.list_by_filters = AsyncMock()
    mock.get_by_tag_at_timestamp = AsyncMock()
    mock.add_calibration = AsyncMock()  # Added from add_calibration_use_case_test
    return mock


@pytest.fixture
def mock_tag_repository() -> AsyncMock:
    """Provides a base mocked TagRepository. Specific methods should be mocked in tests."""
    mock = AsyncMock(spec=TagRepository)
    mock.get_by_id = AsyncMock()
    mock.get_by_name = AsyncMock()
    mock.list_all = AsyncMock()
    mock.add = AsyncMock()

    # Define helper async function for get_by_ids side_effect with correct type hints
    async def _mock_get_by_ids(ids: list[UUID]) -> list[Tag]:
        """Mock implementation for get_by_ids."""
        # Default behaviour: assumes all requested tags exist
        return [create_tag(tag_id=tid) for tid in ids]

    mock.get_by_ids = AsyncMock(side_effect=_mock_get_by_ids)
    return mock
