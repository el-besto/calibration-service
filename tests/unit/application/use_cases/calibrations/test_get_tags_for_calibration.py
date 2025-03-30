from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.dtos.get_tags_for_calibration_dtos import (
    GetTagsForCalibrationInput,
    GetTagsForCalibrationOutput,
)
from src.application.use_cases.calibrations.get_tags_for_calibration import (
    GetTagsForCalibrationUseCase,
)
from src.application.use_cases.exceptions import CalibrationNotFoundError
from src.entities.models.tag import Tag
from tests.utils.entity_factories import (
    create_calibration,
    create_calibration_tag_association,
    create_tag,
)


@pytest.fixture
def get_tags_use_case(
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
) -> GetTagsForCalibrationUseCase:
    """Provides an instance of the GetTagsForCalibrationUseCase."""
    return GetTagsForCalibrationUseCase(
        calibration_repository=mock_calibration_repository,
        tag_repository=mock_tag_repository,
    )


@pytest.mark.asyncio
async def test_get_tags_success(
    get_tags_use_case: GetTagsForCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,  # Uses conftest fixture
    sample_timestamp: datetime,  # Uses conftest fixture
):
    """Test successful retrieval of tags for a calibration."""
    # Arrange
    # Mock calibration existence check
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration

    # Mock associations returned by calibration repo
    assoc1 = create_calibration_tag_association(calibration_id=sample_calibration_id)
    assoc2 = create_calibration_tag_association(calibration_id=sample_calibration_id)
    mock_associations = [assoc1, assoc2]
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = (
        mock_associations
    )

    # Mock tags returned by tag repo based on association IDs
    tag1 = create_tag(tag_id=assoc1.tag_id, name="tag_alpha")
    tag2 = create_tag(tag_id=assoc2.tag_id, name="tag_beta")
    mock_tags = [tag1, tag2]
    mock_tag_repository.get_by_ids.return_value = mock_tags

    # Mock the tag repository to return the specific tags when queried by ID
    async def mock_get_by_ids(ids: list[UUID]) -> list[Tag]:
        # Return tags based on the IDs provided
        return [t for t in [tag1, tag2] if t.id in ids]

    mock_tag_repository.get_by_ids.side_effect = mock_get_by_ids

    input_dto = GetTagsForCalibrationInput(
        calibration_id=sample_calibration_id, timestamp=sample_timestamp
    )
    expected_tag_names = sorted([tag1.name, tag2.name])  # Use case sorts names

    # Act
    result = await get_tags_use_case.execute(input_dto)

    # Assert
    assert isinstance(result, GetTagsForCalibrationOutput)
    assert result.tag_names == expected_tag_names

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        calibration_id=sample_calibration_id, active_at=sample_timestamp
    )
    mock_tag_repository.get_by_ids.assert_awaited_once_with(
        [assoc1.tag_id, assoc2.tag_id]
    )


@pytest.mark.asyncio
async def test_get_tags_no_associations(
    get_tags_use_case: GetTagsForCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_timestamp: datetime,
):
    """Test case where calibration exists but has no active tags."""
    # Arrange
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = []  # No associations

    input_dto = GetTagsForCalibrationInput(
        calibration_id=sample_calibration_id, timestamp=sample_timestamp
    )

    # Act
    result = await get_tags_use_case.execute(input_dto)

    # Assert
    assert isinstance(result, GetTagsForCalibrationOutput)
    assert result.tag_names == []  # Expect empty list

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        calibration_id=sample_calibration_id, active_at=sample_timestamp
    )
    mock_tag_repository.get_by_ids.assert_not_awaited()  # Should not be called if no associations


@pytest.mark.asyncio
async def test_get_tags_calibration_not_found(
    get_tags_use_case: GetTagsForCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_timestamp: datetime,
):
    """Test case where the calibration itself is not found."""
    # Arrange
    mock_calibration_repository.get.return_value = None  # Calibration not found

    input_dto = GetTagsForCalibrationInput(
        calibration_id=sample_calibration_id, timestamp=sample_timestamp
    )

    # Act & Assert
    with pytest.raises(CalibrationNotFoundError):
        await get_tags_use_case.execute(input_dto)

    # Assert mocks
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_not_awaited()
    mock_tag_repository.get_by_ids.assert_not_awaited()
