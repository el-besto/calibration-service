# tests/unit/use_cases/tags/test_get_calibrations_by_tag.py
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.exceptions import TagNotFoundError
from src.application.use_cases.tags.get_calibrations_by_tag import (
    GetCalibrationsByTagInput,
    GetCalibrationsByTagOutput,
    GetCalibrationsByTagUseCase,
)
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.calibration import Calibration
from src.entities.models.tag import Tag
from tests.utils.entity_factories import create_calibration, create_tag


@pytest.fixture
def sample_tag_name() -> str:
    return "test-tag"


@pytest.fixture
def sample_tag(sample_tag_name: str) -> Tag:
    """Provides a sample Tag object."""
    return create_tag(name=sample_tag_name)


@pytest.fixture
def sample_username() -> str:
    return "testuser"


@pytest.fixture
def sample_calibrations(sample_tag: Tag) -> list[Calibration]:
    """Provides a list of sample Calibration objects."""
    cal1 = create_calibration(username="user1", tags=[sample_tag])
    cal2 = create_calibration(username="testuser", tags=[sample_tag])
    cal3 = create_calibration(username="anotheruser", tags=[sample_tag])
    return [cal1, cal2, cal3]


@pytest.fixture
def get_calibrations_use_case(
    mock_tag_repository: AsyncMock, mock_calibration_repository: AsyncMock
) -> GetCalibrationsByTagUseCase:
    """Provides an instance of the GetCalibrationsByTagUseCase."""
    return GetCalibrationsByTagUseCase(
        tag_repository=mock_tag_repository,
        calibration_repository=mock_calibration_repository,
    )


@pytest.mark.asyncio
async def test_get_calibrations_success(
    get_calibrations_use_case: GetCalibrationsByTagUseCase,
    mock_tag_repository: AsyncMock,
    mock_calibration_repository: AsyncMock,
    sample_tag: Tag,
    sample_timestamp: datetime,
    sample_calibrations: list[Calibration],
):
    """Test getting calibrations by tag successfully."""
    # Arrange
    input_data = GetCalibrationsByTagInput(
        tag_name=sample_tag.name, timestamp=sample_timestamp, username=None
    )
    mock_tag_repository.get_by_name.return_value = sample_tag
    mock_calibration_repository.get_by_tag_at_timestamp.return_value = (
        sample_calibrations
    )

    # Act
    result = await get_calibrations_use_case.execute(input_data)

    # Assert
    assert isinstance(result, GetCalibrationsByTagOutput)
    assert result.calibrations == sample_calibrations
    mock_tag_repository.get_by_name.assert_awaited_once_with(sample_tag.name)
    mock_calibration_repository.get_by_tag_at_timestamp.assert_awaited_once_with(
        tag_id=sample_tag.id, timestamp=sample_timestamp, username=None
    )


@pytest.mark.asyncio
async def test_get_calibrations_tag_not_found(
    get_calibrations_use_case: GetCalibrationsByTagUseCase,
    mock_tag_repository: AsyncMock,
    mock_calibration_repository: AsyncMock,
    sample_tag_name: str,
    sample_timestamp: datetime,
):
    """Test getting calibrations when the tag is not found."""
    # Arrange
    input_data = GetCalibrationsByTagInput(
        tag_name=sample_tag_name, timestamp=sample_timestamp, username=None
    )
    mock_tag_repository.get_by_name.return_value = None  # Simulate tag not found

    # Act & Assert
    with pytest.raises(TagNotFoundError):
        await get_calibrations_use_case.execute(input_data)

    mock_tag_repository.get_by_name.assert_awaited_once_with(sample_tag_name)
    mock_calibration_repository.get_by_tag_at_timestamp.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_calibrations_no_calibrations_found(
    get_calibrations_use_case: GetCalibrationsByTagUseCase,
    mock_tag_repository: AsyncMock,
    mock_calibration_repository: AsyncMock,
    sample_tag: Tag,
    sample_timestamp: datetime,
):
    """Test getting calibrations when tag exists but no calibrations are associated."""
    # Arrange
    input_data = GetCalibrationsByTagInput(
        tag_name=sample_tag.name, timestamp=sample_timestamp, username=None
    )
    mock_tag_repository.get_by_name.return_value = sample_tag
    mock_calibration_repository.get_by_tag_at_timestamp.return_value = []  # Simulate no calibrations found

    # Act
    result = await get_calibrations_use_case.execute(input_data)

    # Assert
    assert isinstance(result, GetCalibrationsByTagOutput)
    assert result.calibrations == []
    mock_tag_repository.get_by_name.assert_awaited_once_with(sample_tag.name)
    mock_calibration_repository.get_by_tag_at_timestamp.assert_awaited_once_with(
        tag_id=sample_tag.id, timestamp=sample_timestamp, username=None
    )


@pytest.mark.asyncio
async def test_get_calibrations_with_username_filter(
    get_calibrations_use_case: GetCalibrationsByTagUseCase,
    mock_tag_repository: AsyncMock,
    mock_calibration_repository: AsyncMock,
    sample_tag: Tag,
    sample_timestamp: datetime,
    sample_calibrations: list[Calibration],
    sample_username: str,
):
    """Test getting calibrations by tag with a username filter."""
    # Arrange
    input_data = GetCalibrationsByTagInput(
        tag_name=sample_tag.name, timestamp=sample_timestamp, username=sample_username
    )
    mock_tag_repository.get_by_name.return_value = sample_tag
    # Simulate repository returning only the calibration matching the username
    filtered_calibrations = [
        cal for cal in sample_calibrations if cal.username == sample_username
    ]
    mock_calibration_repository.get_by_tag_at_timestamp.return_value = (
        filtered_calibrations
    )

    # Act
    result = await get_calibrations_use_case.execute(input_data)

    # Assert
    assert isinstance(result, GetCalibrationsByTagOutput)
    assert result.calibrations == filtered_calibrations
    assert len(result.calibrations) == 1
    assert result.calibrations[0].username == sample_username
    mock_tag_repository.get_by_name.assert_awaited_once_with(sample_tag.name)
    mock_calibration_repository.get_by_tag_at_timestamp.assert_awaited_once_with(
        tag_id=sample_tag.id,
        timestamp=sample_timestamp,
        username=sample_username,  # Check username passed
    )


@pytest.mark.asyncio
async def test_get_calibrations_repository_error(
    get_calibrations_use_case: GetCalibrationsByTagUseCase,
    mock_tag_repository: AsyncMock,
    mock_calibration_repository: AsyncMock,
    sample_tag: Tag,
    sample_timestamp: datetime,
):
    """Test handling of DatabaseOperationError from calibration repository."""
    # Arrange
    input_data = GetCalibrationsByTagInput(
        tag_name=sample_tag.name, timestamp=sample_timestamp, username=None
    )
    mock_tag_repository.get_by_name.return_value = sample_tag
    mock_calibration_repository.get_by_tag_at_timestamp.side_effect = (
        DatabaseOperationError("DB read failed")
    )

    # Act & Assert
    with pytest.raises(DatabaseOperationError):
        await get_calibrations_use_case.execute(input_data)

    # Assert mocks
    mock_tag_repository.get_by_name.assert_awaited_once_with(sample_tag.name)
    mock_calibration_repository.get_by_tag_at_timestamp.assert_awaited_once_with(
        tag_id=sample_tag.id, timestamp=sample_timestamp, username=None
    )
