from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
)
from src.application.use_cases.tags.add_tag_to_calibration import (
    AddTagToCalibrationInput,
    AddTagToCalibrationOutput,
    AddTagToCalibrationUseCase,
)
from src.entities.exceptions import DatabaseOperationError
from tests.utils.entity_factories import (
    create_calibration,
    create_tag,
)


@pytest.fixture
def add_tag_use_case(
    mock_calibration_repository: AsyncMock, mock_tag_repository: AsyncMock
) -> AddTagToCalibrationUseCase:
    """Provides an instance of the AddTagToCalibrationUseCase."""
    return AddTagToCalibrationUseCase(
        calibration_repository=mock_calibration_repository,
        tag_repository=mock_tag_repository,
    )


@pytest.mark.asyncio
# Pass fixtures from conftest directly into tests
async def test_add_tag_success(
    add_tag_use_case: AddTagToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
    sample_timestamp: datetime,
):
    """Test successfully adding a tag to a calibration."""

    # Arrange
    input_data = AddTagToCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_tag = create_tag(tag_id=sample_tag_id)

    mock_calibration_repository.get.return_value = mock_calibration
    mock_tag_repository.get_by_id.return_value = mock_tag
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = []

    # Act
    result = await add_tag_use_case.execute(input_data)

    # Assert
    assert isinstance(result, AddTagToCalibrationOutput)
    assert result.association.calibration_id == sample_calibration_id
    assert result.association.tag_id == sample_tag_id
    assert isinstance(result.association.created_at, datetime)
    assert isinstance(result.association.id, UUID)
    assert result.association.archived_at is None
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        calibration_id=sample_calibration_id
    )
    mock_calibration_repository.add_tags.assert_awaited_once()
    _, call_kwargs = mock_calibration_repository.add_tags.call_args
    assert call_kwargs["calibration_id"] == sample_calibration_id
    passed_associations = call_kwargs["calibration_tag_associations"]
    assert len(passed_associations) == 1
    assert passed_associations[0].calibration_id == sample_calibration_id
    assert passed_associations[0].tag_id == sample_tag_id


@pytest.mark.asyncio
async def test_add_tag_calibration_not_found(
    add_tag_use_case: AddTagToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test adding tag when calibration is not found."""

    # Arrange
    input_data = AddTagToCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    # Use the correct exception from use_cases.exceptions
    mock_calibration_repository.get.side_effect = CalibrationNotFoundError(
        f"Calibration with id {sample_calibration_id} not found."
    )
    mock_tag = create_tag(tag_id=sample_tag_id)
    mock_tag_repository.get_by_id.return_value = mock_tag  # Tag exists

    # Act & Assert
    with pytest.raises(CalibrationNotFoundError):
        await add_tag_use_case.execute(input_data)

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_not_awaited()
    mock_calibration_repository.get_tag_associations_for_calibration.assert_not_awaited()
    mock_calibration_repository.add_tags.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_tag_tag_not_found(
    add_tag_use_case: AddTagToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test adding tag when tag is not found."""
    # Arrange
    input_data = AddTagToCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration  # Calib exists
    # Use the correct exception from use_cases.exceptions
    mock_tag_repository.get_by_id.side_effect = TagNotFoundError(
        f"Tag with id {sample_tag_id} not found."
    )

    # Act & Assert
    with pytest.raises(TagNotFoundError):
        await add_tag_use_case.execute(input_data)

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_not_awaited()
    mock_calibration_repository.add_tags.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_tag_already_associated(  # Renamed for clarity: Now tests repository error
    add_tag_use_case: AddTagToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test handling DatabaseOperationError when adding an already associated tag."""
    # Arrange
    input_data = AddTagToCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_tag = create_tag(tag_id=sample_tag_id)

    mock_calibration_repository.get.return_value = mock_calibration
    mock_tag_repository.get_by_id.return_value = mock_tag
    # Use case checks existing first, let's assume none are active
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = []
    # Mock add_tags to raise the error
    mock_calibration_repository.add_tags.side_effect = DatabaseOperationError(
        "Simulated error: Failed to add association (e.g., unique constraint)"
    )

    # Act & Assert
    # Expect a DatabaseOperationError, not a specific TagAlreadyAssociatedError
    with pytest.raises(DatabaseOperationError):
        await add_tag_use_case.execute(input_data)

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        calibration_id=sample_calibration_id
    )
    mock_calibration_repository.add_tags.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_tag_repository_add_error(
    add_tag_use_case: AddTagToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test handling of DatabaseOperationError during repository add_tag_association."""
    # Arrange
    input_data = AddTagToCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_tag = create_tag(tag_id=sample_tag_id)

    mock_calibration_repository.get.return_value = mock_calibration
    mock_tag_repository.get_by_id.return_value = mock_tag
    # Assume no existing active associations
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = []
    # Mock add_tags to raise the error
    mock_calibration_repository.add_tags.side_effect = DatabaseOperationError(
        "DB write failed"
    )

    # Act & Assert
    with pytest.raises(DatabaseOperationError):
        await add_tag_use_case.execute(input_data)

    # Assert
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        calibration_id=sample_calibration_id
    )
    mock_calibration_repository.add_tags.assert_awaited_once()
