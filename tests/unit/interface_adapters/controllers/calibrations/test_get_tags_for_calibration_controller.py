from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from src.application.dtos.get_tags_for_calibration_dtos import (
    GetTagsForCalibrationInput,
    GetTagsForCalibrationOutput,
)
from src.application.use_cases.calibrations.get_tags_for_calibration import (
    GetTagsForCalibrationUseCase,
)
from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    UseCaseError,
)
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.interface_adapters.controllers.calibrations.get_tags_for_calibration_controller import (
    GetTagsForCalibrationController,
)
from src.interface_adapters.presenters.calibration_presenter import CalibrationPresenter


@pytest.fixture
def mock_get_tags_use_case() -> AsyncMock:
    return AsyncMock(spec=GetTagsForCalibrationUseCase)


@pytest.fixture
def get_tags_controller(
    mock_get_tags_use_case: AsyncMock,
) -> GetTagsForCalibrationController:
    return GetTagsForCalibrationController(
        get_tags_for_calibration_use_case=mock_get_tags_use_case
    )


@pytest.fixture
def sample_calibration_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_timestamp() -> datetime:
    # Use timezone-aware datetime
    return datetime.now(UTC)


@pytest.mark.asyncio
async def test_get_tags_for_calibration_success(
    get_tags_controller: GetTagsForCalibrationController,
    mock_get_tags_use_case: AsyncMock,
    sample_calibration_id: UUID,
    sample_timestamp: datetime,
):
    """Test successful retrieval of tags for a calibration."""
    # Arrange
    tag_list = ["tag1", "tag2", "beta"]
    mock_output = GetTagsForCalibrationOutput(tag_names=tag_list)
    mock_get_tags_use_case.execute.return_value = mock_output

    # Mock presenter
    expected_response = sorted(tag_list)  # Presenter sorts the tags

    # Use patch.object to mock the static/class method
    with patch.object(
        CalibrationPresenter,
        "present_calibration_tags",
        return_value=expected_response,
    ) as mock_present_method: # This context manager yields the mock replacement
        # Act
        response = await get_tags_controller.get_tags_for_calibration(
            calibration_id=sample_calibration_id, timestamp=sample_timestamp
        )

        # Assert
        mock_get_tags_use_case.execute.assert_awaited_once()
        call_args = mock_get_tags_use_case.execute.call_args[0][0]
        assert isinstance(call_args, GetTagsForCalibrationInput)
        assert call_args.calibration_id == sample_calibration_id
        assert call_args.timestamp == sample_timestamp

        # Assert that the *patched method* was called
        mock_present_method.assert_called_once_with(mock_output)
        assert response == expected_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_type, expected_exception",
    [
        (CalibrationNotFoundError("Calibration not found"), NotFoundError),
        (DatabaseOperationError("DB connection failed"), DatabaseOperationError),
        (UseCaseError("Internal logic error"), UseCaseError),
        (ValueError("Unexpected"), UseCaseError),  # Test generic exception handling
        (Exception("Completely unexpected"), UseCaseError),  # Test base Exception catch
    ],
)
async def test_get_tags_for_calibration_exceptions(
    get_tags_controller: GetTagsForCalibrationController,
    mock_get_tags_use_case: AsyncMock,
    sample_calibration_id: UUID,
    sample_timestamp: datetime,
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test controller exception handling during tag retrieval."""
    # Arrange
    mock_get_tags_use_case.execute.side_effect = error_type

    # Act & Assert
    with pytest.raises(expected_exception):
        await get_tags_controller.get_tags_for_calibration(
            calibration_id=sample_calibration_id, timestamp=sample_timestamp
        )

    mock_get_tags_use_case.execute.assert_awaited_once()
    # Verify arguments passed to the use case mock
    call_args = mock_get_tags_use_case.execute.call_args[0][0]
    assert isinstance(call_args, GetTagsForCalibrationInput)
    assert call_args.calibration_id == sample_calibration_id
    assert call_args.timestamp == sample_timestamp
