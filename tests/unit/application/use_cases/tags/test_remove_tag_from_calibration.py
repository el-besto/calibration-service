# tests/unit/use_cases/tags/test_remove_tag_from_calibration.py
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.use_cases.exceptions import (
    AssociationNotFoundError,
    CalibrationNotFoundError,
    TagNotFoundError,
)
from src.application.use_cases.tags.remove_tag_from_calibration import (
    RemoveTagFromCalibrationInput,
    RemoveTagFromCalibrationOutput,
    RemoveTagFromCalibrationUseCase,
)
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from tests.utils.entity_factories import (
    create_calibration,
    create_calibration_tag_association,
    create_tag,
)


@pytest.fixture
def sample_association(
    sample_calibration_id: UUID,
    sample_tag_id: UUID,  # These now come from conftest
) -> CalibrationTagAssociation:
    """Creates a sample, active association."""
    return create_calibration_tag_association(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id, archived_at=None
    )


@pytest.fixture
def remove_tag_use_case(
    mock_calibration_repository: AsyncMock, mock_tag_repository: AsyncMock
) -> RemoveTagFromCalibrationUseCase:
    """Provides an instance of the RemoveTagFromCalibrationUseCase."""
    return RemoveTagFromCalibrationUseCase(
        calibration_repository=mock_calibration_repository,
        tag_repository=mock_tag_repository,
    )


@pytest.mark.asyncio
# Pass fixtures from conftest
async def test_remove_tag_success(
    remove_tag_use_case: RemoveTagFromCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
    sample_association: CalibrationTagAssociation,
):
    """Test successfully removing (archiving) a tag association."""
    # Arrange
    input_data = RemoveTagFromCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_tag = create_tag(tag_id=sample_tag_id)

    # Mock repository responses
    mock_calibration_repository.get.return_value = mock_calibration
    mock_tag_repository.get_by_id.return_value = mock_tag
    # Return the specific association when fetching active ones
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = [
        sample_association
    ]
    # Simulate the update returning the modified (archived) association
    # We need to mock the 'archive' method call on the association itself
    archived_association = create_calibration_tag_association(
        association_id=sample_association.id,
        calibration_id=sample_calibration_id,
        tag_id=sample_tag_id,
        created_at=sample_association.created_at,
        archived_at=datetime.now(UTC),  # Set archive time
    )
    # Mock the 'archive' method to modify the object state implicitly for the test
    # sample_association.archive = MagicMock() # Not strictly needed if repo returns the final state

    mock_calibration_repository.update_tag_association.return_value = (
        archived_association
    )

    # Act
    result = await remove_tag_use_case.execute(input_data)

    # Assert
    assert isinstance(result, RemoveTagFromCalibrationOutput)
    assert result.archived_association == archived_association
    assert result.archived_association.is_archived is True  # Verify it's archived
    assert result.archived_association.archived_at is not None

    # Verify mock calls
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once()
    # Check call args for get_tag_associations_for_calibration if needed (e.g., active_at time)
    mock_calibration_repository.update_tag_association.assert_awaited_once()
    # Check the association passed to update had archive() called (state updated)
    updated_arg = mock_calibration_repository.update_tag_association.call_args[0][0]
    assert isinstance(updated_arg, CalibrationTagAssociation)
    assert updated_arg.id == sample_association.id
    # In a real scenario, the use case calls `archive()` which sets `archived_at`.
    # We check the mock was called with an object *representing* that state.
    assert updated_arg.archived_at is not None


@pytest.mark.asyncio
async def test_remove_tag_calibration_not_found(
    remove_tag_use_case: RemoveTagFromCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test removing tag when calibration is not found."""
    # Arrange
    input_data = RemoveTagFromCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration_repository.get.side_effect = CalibrationNotFoundError(
        f"Calibration with id {sample_calibration_id} not found."
    )

    # Act & Assert
    with pytest.raises(CalibrationNotFoundError):
        await remove_tag_use_case.execute(input_data)

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_not_awaited()  # Should fail before tag check
    mock_calibration_repository.get_tag_associations_for_calibration.assert_not_awaited()
    mock_calibration_repository.update_tag_association.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_tag_tag_not_found(
    remove_tag_use_case: RemoveTagFromCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test removing tag when tag is not found."""
    # Arrange
    input_data = RemoveTagFromCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_calibration_repository.get.return_value = (
        mock_calibration  # Calibration exists
    )
    mock_tag_repository.get_by_id.side_effect = TagNotFoundError(
        f"Tag with id {sample_tag_id} not found."
    )

    # Act & Assert
    with pytest.raises(TagNotFoundError):
        await remove_tag_use_case.execute(input_data)

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_not_awaited()
    mock_calibration_repository.update_tag_association.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_tag_association_not_found(
    remove_tag_use_case: RemoveTagFromCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test removing tag when no active association exists."""
    # Arrange
    input_data = RemoveTagFromCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_tag = create_tag(tag_id=sample_tag_id)

    mock_calibration_repository.get.return_value = mock_calibration
    mock_tag_repository.get_by_id.return_value = mock_tag
    # Simulate no active associations returned
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = []

    # Act & Assert
    with pytest.raises(AssociationNotFoundError):
        await remove_tag_use_case.execute(input_data)

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once()
    mock_calibration_repository.update_tag_association.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_tag_association_already_archived(
    remove_tag_use_case: RemoveTagFromCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
):
    """Test removing tag when the association is already archived (should raise AssociationNotFound)."""
    # Arrange
    input_data = RemoveTagFromCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_tag = create_tag(tag_id=sample_tag_id)
    # Create an association that is already archived
    already_archived_association = create_calibration_tag_association(
        calibration_id=sample_calibration_id,
        tag_id=sample_tag_id,
        archived_at=datetime.now(UTC) - timedelta(days=1),  # Archived yesterday
    )

    mock_calibration_repository.get.return_value = mock_calibration
    mock_tag_repository.get_by_id.return_value = mock_tag
    # Simulate the repository returning only the already archived association
    # The use case logic specifically looks for *active* associations to archive.
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = [
        already_archived_association
    ]

    # Act & Assert
    # Since the use case looks for an *active* association to archive, finding none should
    # result in AssociationNotFoundError
    with pytest.raises(AssociationNotFoundError):
        await remove_tag_use_case.execute(input_data)

    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once()
    mock_calibration_repository.update_tag_association.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_tag_repository_update_error(
    remove_tag_use_case: RemoveTagFromCalibrationUseCase,
    mock_calibration_repository: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    sample_tag_id: UUID,
    sample_association: CalibrationTagAssociation,
):
    """Test handling of DatabaseOperationError during repository update."""
    # Arrange
    input_data = RemoveTagFromCalibrationInput(
        calibration_id=sample_calibration_id, tag_id=sample_tag_id
    )
    mock_calibration = create_calibration(calibration_id=sample_calibration_id)
    mock_tag = create_tag(tag_id=sample_tag_id)

    mock_calibration_repository.get.return_value = mock_calibration
    mock_tag_repository.get_by_id.return_value = mock_tag
    mock_calibration_repository.get_tag_associations_for_calibration.return_value = [
        sample_association
    ]
    # Simulate DB error during the update step
    mock_calibration_repository.update_tag_association.side_effect = (
        DatabaseOperationError("DB update failed")
    )

    # Act & Assert
    with pytest.raises(DatabaseOperationError):
        await remove_tag_use_case.execute(input_data)

    # Assert
    mock_calibration_repository.get.assert_awaited_once_with(id=sample_calibration_id)
    mock_tag_repository.get_by_id.assert_awaited_once_with(sample_tag_id)
    mock_calibration_repository.get_tag_associations_for_calibration.assert_awaited_once()
    mock_calibration_repository.update_tag_association.assert_awaited_once()
