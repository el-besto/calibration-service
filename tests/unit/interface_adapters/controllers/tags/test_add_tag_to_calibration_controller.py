# tests/unit/interface_adapters/controllers/tags/test_add_tag_to_calibration_controller.py
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
    UseCaseError,
)
from src.application.use_cases.tags.add_tag_to_calibration import (
    AddTagToCalibrationInput,
    AddTagToCalibrationUseCase,
)
from src.application.use_cases.tags.create_tag import (
    CreateTagInput,
    CreateTagOutput,
    CreateTagUseCase,
)
from src.drivers.rest.schemas.tag_schemas import (
    TagOperationRequest,
    TagOperationResponse,
)
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.entities.models.tag import Tag
from src.interface_adapters.controllers.tags.add_tag_to_calibration_controller import (
    AddTagToCalibrationController,
)
from src.interface_adapters.presenters.tag_presenter import TagPresenter


@pytest.fixture
def mock_add_tag_use_case() -> AsyncMock:
    return AsyncMock(spec=AddTagToCalibrationUseCase)


@pytest.fixture
def mock_create_tag_use_case() -> AsyncMock:
    return AsyncMock(spec=CreateTagUseCase)


@pytest.fixture
def add_tag_controller(
    mock_add_tag_use_case: AsyncMock,
    mock_create_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
) -> AddTagToCalibrationController:
    return AddTagToCalibrationController(
        add_tag_use_case=mock_add_tag_use_case,
        create_tag_use_case=mock_create_tag_use_case,
        tag_repository=mock_tag_repository,
    )


# Expected successful response from presenter
@pytest.fixture
def expected_success_response() -> TagOperationResponse:
    # We mock the presenter directly, so the exact content matters less
    # than the object type for this fixture. Let's assume a standard success message.
    return TagOperationResponse(message="Tag added successfully.")


# --- Test Cases ---


@pytest.mark.asyncio
async def test_add_tag_tag_exists(
    add_tag_controller: AddTagToCalibrationController,
    mock_add_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
    mock_create_tag_use_case: AsyncMock,  # Needed for fixture, but not called
    sample_calibration_id: UUID,
    valid_request: TagOperationRequest,
    sample_tag: Tag,
    expected_success_response: TagOperationResponse,
):
    """Test adding a tag when the tag already exists."""
    # Arrange
    mock_tag_repository.get_by_name.return_value = sample_tag  # Tag found by name
    mock_add_tag_use_case.execute.return_value = (
        None  # Assume success, no specific output needed
    )

    with patch.object(
        TagPresenter, "present_tag_added", return_value=expected_success_response
    ) as mock_presenter:
        # Act
        response = await add_tag_controller.add_tag_to_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

        # Assert
        mock_tag_repository.get_by_name.assert_awaited_once_with(valid_request.tag)
        mock_create_tag_use_case.execute.assert_not_awaited()  # Should not be called
        mock_add_tag_use_case.execute.assert_awaited_once()
        # Check input DTO passed to add_tag_use_case
        call_args = mock_add_tag_use_case.execute.call_args[0][0]
        assert isinstance(call_args, AddTagToCalibrationInput)
        assert call_args.calibration_id == sample_calibration_id
        assert call_args.tag_id == sample_tag.id  # ID from existing tag

        mock_presenter.assert_called_once()
        assert response == expected_success_response


@pytest.mark.asyncio
async def test_add_tag_tag_created(
    add_tag_controller: AddTagToCalibrationController,
    mock_add_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
    mock_create_tag_use_case: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: TagOperationRequest,
    sample_tag: Tag,  # Use sample_tag fixture for the *created* tag
    expected_success_response: TagOperationResponse,
):
    """Test adding a tag when the tag needs to be created."""
    # Arrange
    mock_tag_repository.get_by_name.return_value = None  # Tag not found initially
    mock_create_tag_output = CreateTagOutput(tag=sample_tag)
    mock_create_tag_use_case.execute.return_value = mock_create_tag_output
    mock_add_tag_use_case.execute.return_value = None  # Assume success

    with patch.object(
        TagPresenter, "present_tag_added", return_value=expected_success_response
    ) as mock_presenter:
        # Act
        response = await add_tag_controller.add_tag_to_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

        # Assert
        mock_tag_repository.get_by_name.assert_awaited_once_with(valid_request.tag)
        mock_create_tag_use_case.execute.assert_awaited_once()
        # Check input DTO passed to create_tag_use_case
        create_call_args = mock_create_tag_use_case.execute.call_args[0][0]
        assert isinstance(create_call_args, CreateTagInput)
        assert create_call_args.name == valid_request.tag

        mock_add_tag_use_case.execute.assert_awaited_once()
        # Check input DTO passed to add_tag_use_case
        add_call_args = mock_add_tag_use_case.execute.call_args[0][0]
        assert isinstance(add_call_args, AddTagToCalibrationInput)
        assert add_call_args.calibration_id == sample_calibration_id
        assert add_call_args.tag_id == sample_tag.id  # ID from *created* tag

        mock_presenter.assert_called_once()
        assert response == expected_success_response


@pytest.mark.asyncio
async def test_add_tag_get_or_create_race_condition(
    add_tag_controller: AddTagToCalibrationController,
    mock_add_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
    mock_create_tag_use_case: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: TagOperationRequest,
    sample_tag: Tag,
    expected_success_response: TagOperationResponse,
):
    """Test the race condition handling in _get_or_create_tag."""
    # Arrange
    # First get_by_name returns None
    # create_tag raises DB error indicating existence
    # Second get_by_name returns the tag
    mock_tag_repository.get_by_name.side_effect = [None, sample_tag]
    mock_create_tag_use_case.execute.side_effect = DatabaseOperationError(
        "already exists"
    )
    mock_add_tag_use_case.execute.return_value = None

    with patch.object(
        TagPresenter, "present_tag_added", return_value=expected_success_response
    ) as mock_presenter:
        # Act
        response = await add_tag_controller.add_tag_to_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

        # Assert
        assert mock_tag_repository.get_by_name.await_count == 2
        mock_create_tag_use_case.execute.assert_awaited_once()
        mock_add_tag_use_case.execute.assert_awaited_once()
        # Ensure the final tag ID used was from the second get_by_name call
        add_call_args = mock_add_tag_use_case.execute.call_args[0][0]
        assert add_call_args.tag_id == sample_tag.id
        mock_presenter.assert_called_once()
        assert response == expected_success_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_origin, error_type, expected_exception",
    [
        # Errors from _get_or_create_tag part
        (
            "repo_get",
            DatabaseOperationError("Initial DB error"),
            DatabaseOperationError,
        ),
        ("create_use_case", UseCaseError("Create failed"), UseCaseError),
        (
            "create_use_case",
            DatabaseOperationError("Create DB failed"),
            DatabaseOperationError,
        ),
        # Errors from add_tag_use_case part (after successful get_or_create)
        ("add_use_case", CalibrationNotFoundError("Cal not found"), NotFoundError),
        (
            "add_use_case",
            TagNotFoundError("Tag somehow not found by ID"),
            NotFoundError,
        ),  # Should map to NotFoundError
        ("add_use_case", DatabaseOperationError("Add failed"), DatabaseOperationError),
        ("add_use_case", UseCaseError("Add internal error"), UseCaseError),
        # Generic error
        ("add_use_case", Exception("Completely unexpected"), UseCaseError),
    ],
)
async def test_add_tag_exceptions(
    add_tag_controller: AddTagToCalibrationController,
    mock_add_tag_use_case: AsyncMock,
    mock_tag_repository: AsyncMock,
    mock_create_tag_use_case: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: TagOperationRequest,
    sample_tag: Tag,
    error_origin: str,
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test various exception scenarios during add tag."""
    # Arrange
    if error_origin == "repo_get":
        mock_tag_repository.get_by_name.side_effect = error_type
    elif error_origin == "create_use_case":
        mock_tag_repository.get_by_name.return_value = None  # Simulate tag not found
        mock_create_tag_use_case.execute.side_effect = error_type
    elif error_origin == "add_use_case":
        # Simulate successful get_or_create first
        mock_tag_repository.get_by_name.return_value = sample_tag
        mock_add_tag_use_case.execute.side_effect = error_type
    else:  # Should not happen
        pytest.fail("Invalid error_origin specified in test parameterization")

    # Act & Assert
    with pytest.raises(expected_exception):
        await add_tag_controller.add_tag_to_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

    # Assert mocks were called appropriately
    mock_tag_repository.get_by_name.assert_awaited()
    if error_origin == "create_use_case":
        mock_create_tag_use_case.execute.assert_awaited()
        mock_add_tag_use_case.execute.assert_not_awaited()
    elif error_origin == "add_use_case":
        # Might have called create_tag if get_by_name returned None initially,
        # but the error occurs in add_tag_use_case
        mock_add_tag_use_case.execute.assert_awaited()
    # If error was in repo_get, neither use case should be called
    elif error_origin == "repo_get":
        mock_create_tag_use_case.execute.assert_not_awaited()
        mock_add_tag_use_case.execute.assert_not_awaited()
