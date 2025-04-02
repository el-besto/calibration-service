from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from src.application.use_cases.exceptions import (
    AssociationNotFoundError,
    CalibrationNotFoundError,
    TagNotFoundError,
    UseCaseError,
)
from src.application.use_cases.tags.remove_tag_from_calibration import (
    RemoveTagFromCalibrationInput,
    RemoveTagFromCalibrationUseCase,
)
from src.drivers.rest.schemas.tag_schemas import (
    TagOperationRequest,
    TagOperationResponse,
)
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.entities.models.tag import Tag
from src.interface_adapters.controllers.tags.remove_tag_from_calibration_controller import (
    RemoveTagFromCalibrationController,
)
from src.interface_adapters.presenters.tag_presenter import TagPresenter


@pytest.fixture
def mock_remove_tag_use_case() -> AsyncMock:
    return AsyncMock(spec=RemoveTagFromCalibrationUseCase)


@pytest.fixture
def remove_tag_controller(
    mock_remove_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
) -> RemoveTagFromCalibrationController:
    return RemoveTagFromCalibrationController(
        remove_tag_use_case=mock_remove_tag_use_case,
        tag_repository=mock_tag_repository,
    )


# Expected successful response from presenter
@pytest.fixture
def expected_success_response() -> TagOperationResponse:
    return TagOperationResponse(message="Tag removed successfully.")


# --- Test Cases ---


@pytest.mark.asyncio
async def test_remove_tag_success(
    remove_tag_controller: RemoveTagFromCalibrationController,
    mock_remove_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: TagOperationRequest,
    sample_tag: Tag,
    expected_success_response: TagOperationResponse,
):
    """Test successful tag removal."""
    # Arrange
    mock_tag_repository.get_by_name.return_value = sample_tag  # Tag found
    # Assume use case succeeds (output DTO might be None or contain archived assoc.)
    mock_remove_tag_use_case.execute.return_value = None

    with patch.object(
        TagPresenter, "present_tag_removed", return_value=expected_success_response
    ) as mock_presenter:
        # Act
        response = await remove_tag_controller.remove_tag_from_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

        # Assert
        mock_tag_repository.get_by_name.assert_awaited_once_with(valid_request.tag)
        mock_remove_tag_use_case.execute.assert_awaited_once()
        # Check input DTO passed to remove_tag_use_case
        call_args = mock_remove_tag_use_case.execute.call_args[0][0]
        assert isinstance(call_args, RemoveTagFromCalibrationInput)
        assert call_args.calibration_id == sample_calibration_id
        assert call_args.tag_id == sample_tag.id  # ID from tag found by name

        mock_presenter.assert_called_once()
        assert response == expected_success_response


@pytest.mark.asyncio
async def test_remove_tag_tag_not_found_by_name(
    remove_tag_controller: RemoveTagFromCalibrationController,
    mock_remove_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: TagOperationRequest,
):
    """Test removing a tag when the tag name itself is not found."""
    # Arrange
    mock_tag_repository.get_by_name.return_value = None  # Tag not found by name

    # Act & Assert
    with pytest.raises(NotFoundError, match=f"Tag '{valid_request.tag}' not found."):
        await remove_tag_controller.remove_tag_from_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

    # Assert
    mock_tag_repository.get_by_name.assert_awaited_once_with(valid_request.tag)
    mock_remove_tag_use_case.execute.assert_not_awaited()  # Use case not called


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_origin", "error_type", "expected_exception"),
    [
        # Error from repository before use case call
        (
            "repo_get",
            DatabaseOperationError("DB error finding tag"),
            DatabaseOperationError,
        ),
        # Errors from use case execution
        ("use_case", CalibrationNotFoundError("Cal not found"), NotFoundError),
        (
            "use_case",
            TagNotFoundError("Tag ID not found by use case"),
            NotFoundError,
        ),  # Should map to NotFoundError
        (
            "use_case",
            AssociationNotFoundError("No active assoc found"),
            NotFoundError,
        ),  # Should map to NotFoundError
        (
            "use_case",
            DatabaseOperationError("DB error archiving"),
            DatabaseOperationError,
        ),
        ("use_case", UseCaseError("Internal logic error"), UseCaseError),
        # Generic error
        ("use_case", Exception("Completely unexpected"), UseCaseError),
    ],
)
async def test_remove_tag_exceptions(
    remove_tag_controller: RemoveTagFromCalibrationController,
    mock_remove_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: TagOperationRequest,
    sample_tag: Tag,
    error_origin: str,
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test various exception scenarios during tag removal."""
    # Arrange
    if error_origin == "repo_get":
        mock_tag_repository.get_by_name.side_effect = error_type
    elif error_origin == "use_case":
        mock_tag_repository.get_by_name.return_value = (
            sample_tag  # Simulate tag found by name
        )
        mock_remove_tag_use_case.execute.side_effect = error_type
    else:
        pytest.fail("Invalid error_origin")

    # Act & Assert
    with pytest.raises(expected_exception):
        await remove_tag_controller.remove_tag_from_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

    # Assert mocks were called appropriately
    mock_tag_repository.get_by_name.assert_awaited()
    if error_origin == "use_case":
        mock_remove_tag_use_case.execute.assert_awaited_once()
        call_args = mock_remove_tag_use_case.execute.call_args[0][0]
        assert call_args.tag_id == sample_tag.id  # Ensure correct tag ID was passed
    elif error_origin == "repo_get":
        mock_remove_tag_use_case.execute.assert_not_awaited()
