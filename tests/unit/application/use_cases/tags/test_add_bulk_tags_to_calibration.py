from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
    ValidationError,
)
from src.application.use_cases.tags.add_bulk_tags_to_calibration import (
    AddBulkTagsToCalibrationInput,
    AddBulkTagsToCalibrationOutput,
    AddBulkTagsToCalibrationUseCase,
)
from src.entities.exceptions import DatabaseOperationError
from tests.utils.entity_factories import (
    create_calibration,
    create_calibration_tag_association,
    create_tag,
)


@pytest.fixture
def sample_tag_ids() -> list[UUID]:
    """Provides a list of sample tag IDs."""
    return [uuid4() for _ in range(3)]


@pytest.fixture
def add_bulk_tags_use_case(
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
) -> AddBulkTagsToCalibrationUseCase:
    """Provides an instance of the AddBulkTagsToCalibrationUseCase."""
    return AddBulkTagsToCalibrationUseCase(
        calibration_repository=mock_calibration_repository,
        tag_repository=mock_tag_repository,
    )


@pytest.mark.asyncio
async def test_add_bulk_tags_success_all_new(
    add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_ids: list[UUID],
):
    """Test adding multiple new tags successfully."""
    # Arrange
    input_data = AddBulkTagsToCalibrationInput(
        calibration_id=sample_calibration_id, tag_ids=sample_tag_ids
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration
    mock_tags = [create_tag(tag_id=tid) for tid in sample_tag_ids]
    mock_tag_repository.get_by_ids.return_value = mock_tags
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = []

    # Act
    result = await add_bulk_tags_use_case(input_data)

    # Assert
    assert isinstance(result, AddBulkTagsToCalibrationOutput)
    assert len(result.added_associations) == len(sample_tag_ids)
    assert len(result.skipped_tag_ids) == 0
    added_tag_ids = {assoc.tag_id for assoc in result.added_associations}
    assert added_tag_ids == set(sample_tag_ids)

    # Verify mocks
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_ids.assert_awaited_once_with(
        list(set(sample_tag_ids))
    )  # Use case might dedupe
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        sample_calibration_id
    )
    mock_calibration_repository.add_tags.assert_awaited_once()
    # Check the associations passed to add_tags
    _, call_kwargs = mock_calibration_repository.add_tags.call_args  # Get kwargs
    assert call_kwargs["calibration_id"] == sample_calibration_id
    passed_associations = call_kwargs["calibration_tag_associations"]
    assert len(passed_associations) == len(sample_tag_ids)
    assert {assoc.tag_id for assoc in passed_associations} == set(sample_tag_ids)


@pytest.mark.asyncio
async def test_add_bulk_tags_success_some_existing(
    add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_ids: list[UUID],
):
    """Test adding tags where some are already actively associated."""
    # Arrange
    input_data = AddBulkTagsToCalibrationInput(
        calibration_id=sample_calibration_id, tag_ids=sample_tag_ids
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration
    mock_tags = [create_tag(tag_id=tid) for tid in sample_tag_ids]
    mock_tag_repository.get_by_ids.return_value = mock_tags

    # Simulate one tag already being associated and active
    existing_tag_id = sample_tag_ids[0]
    new_tag_ids = sample_tag_ids[1:]
    existing_association = create_calibration_tag_association(
        calibration_id=sample_calibration_id, tag_id=existing_tag_id, archived_at=None
    )
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = [
        existing_association
    ]

    # Act
    result = await add_bulk_tags_use_case(input_data)

    # Assert
    assert isinstance(result, AddBulkTagsToCalibrationOutput)
    assert len(result.added_associations) == len(new_tag_ids)
    assert result.skipped_tag_ids == [existing_tag_id]
    added_tag_ids = {assoc.tag_id for assoc in result.added_associations}
    assert added_tag_ids == set(new_tag_ids)

    # Verify mocks
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_ids.assert_awaited_once_with(list(set(sample_tag_ids)))
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        sample_calibration_id
    )
    # add_tags should only be called with the *new* associations
    mock_calibration_repository.add_tags.assert_awaited_once()
    _, call_kwargs = mock_calibration_repository.add_tags.call_args  # Get kwargs
    assert call_kwargs["calibration_id"] == sample_calibration_id
    passed_associations = call_kwargs["calibration_tag_associations"]
    assert len(passed_associations) == len(new_tag_ids)
    assert {assoc.tag_id for assoc in passed_associations} == set(new_tag_ids)


@pytest.mark.asyncio
async def test_add_bulk_tags_success_all_existing(
    add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_ids: list[UUID],
):
    """Test adding tags where all are already actively associated."""
    # Arrange
    input_data = AddBulkTagsToCalibrationInput(
        calibration_id=sample_calibration_id, tag_ids=sample_tag_ids
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration
    mock_tags = [create_tag(tag_id=tid) for tid in sample_tag_ids]
    mock_tag_repository.get_by_ids.return_value = mock_tags

    # Simulate all tags already being associated and active
    existing_associations = [
        create_calibration_tag_association(
            calibration_id=sample_calibration_id, tag_id=tag_id, archived_at=None
        )
        for tag_id in sample_tag_ids
    ]
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = (
        existing_associations
    )

    # Act
    result = await add_bulk_tags_use_case(input_data)

    # Assert
    assert isinstance(result, AddBulkTagsToCalibrationOutput)
    assert len(result.added_associations) == 0
    assert set(result.skipped_tag_ids) == set(sample_tag_ids)  # Order doesn't matter

    # Verify mocks
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_ids.assert_awaited_once_with(list(set(sample_tag_ids)))
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        sample_calibration_id
    )
    # add_tags should NOT be called if no new associations are needed
    mock_calibration_repository.add_tags.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_bulk_tags_calibration_not_found(
    add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_ids: list[UUID],
):
    """Test adding bulk tags when the calibration is not found."""
    # Arrange
    input_data = AddBulkTagsToCalibrationInput(
        calibration_id=sample_calibration_id, tag_ids=sample_tag_ids
    )
    mock_calibration_repository.get.side_effect = CalibrationNotFoundError(
        f"Calibration {sample_calibration_id} not found"
    )

    # Act & Assert
    with pytest.raises(CalibrationNotFoundError):
        await add_bulk_tags_use_case(input_data)

    # Verify mocks
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)


@pytest.mark.asyncio
async def test_add_bulk_tags_some_tags_not_found(
    add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_ids: list[UUID],
):
    """Test adding bulk tags when some tag IDs are not found."""
    # Arrange
    input_data = AddBulkTagsToCalibrationInput(
        calibration_id=sample_calibration_id, tag_ids=sample_tag_ids
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration

    # Simulate tag repository returning fewer tags than requested
    found_tag_ids = sample_tag_ids[:-1]  # All but the last one
    not_found_id = sample_tag_ids[-1]
    mock_tag_repository.get_by_ids.return_value = [
        create_tag(tag_id=tid) for tid in found_tag_ids
    ]

    # Act & Assert
    with pytest.raises(TagNotFoundError) as exc_info:
        await add_bulk_tags_use_case(input_data)

    assert str(not_found_id) in str(
        exc_info.value
    )  # Check if the missing ID is in the error message

    # Verify mocks
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_ids.assert_awaited_once_with(list(set(sample_tag_ids)))
    # Should fail before getting associations or adding tags
    mock_calibration_repository.get_tag_associations_for_calibration.assert_not_awaited()
    mock_calibration_repository.add_tags.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_bulk_tags_raises_validation_error_empty_list(
    add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    sample_calibration_id: UUID,
):
    """Test adding bulk tags with an empty list raises ValidationError."""
    # Arrange
    sample_calibration_id = uuid4()  # Need a calibration ID for input
    input_data = AddBulkTagsToCalibrationInput(
        calibration_id=sample_calibration_id,
        tag_ids=[],  # Empty list
    )
    # Act & Assert
    with pytest.raises(ValidationError, match="List of tag IDs cannot be empty."):
        await add_bulk_tags_use_case(input_data)
    # No mocks should be called as validation fails first


@pytest.mark.asyncio
async def test_add_bulk_tags_repository_add_tags_error(
    add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_ids: list[UUID],
):
    """Test handling of DatabaseOperationError during repository add_tags."""
    # Arrange
    input_data = AddBulkTagsToCalibrationInput(
        calibration_id=sample_calibration_id, tag_ids=sample_tag_ids
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = mock_calibration
    mock_tags = [create_tag(tag_id=tid) for tid in sample_tag_ids]
    mock_tag_repository.get_by_ids.return_value = mock_tags
    # Assume tags exist and no existing associations for simplicity
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = []
    # Simulate DB error during the add_tags step
    mock_calibration_repository.add_tags.side_effect = DatabaseOperationError(
        "DB add_tags failed"
    )

    # Act & Assert
    with pytest.raises(DatabaseOperationError):
        await add_bulk_tags_use_case(input_data)

    # Verify mocks up to the point of failure
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_ids.assert_awaited_once_with(list(set(sample_tag_ids)))
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once_with(
        sample_calibration_id
    )
    mock_calibration_repository.add_tags.assert_awaited_once()  # It was called, but failed
