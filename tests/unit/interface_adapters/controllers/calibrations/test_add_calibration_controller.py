from unittest.mock import AsyncMock, patch

import pytest

from src.application.use_cases.calibrations.add_calibration_use_case import (
    AddCalibrationInput,
    AddCalibrationOutput,
    AddCalibrationUseCase,
)
from src.application.use_cases.exceptions import UseCaseError
from src.drivers.rest.schemas.calibration_schemas import (
    CalibrationCreateRequest,
    CalibrationCreateResponse,
)
from src.entities.exceptions import DatabaseOperationError, InputParseError
from src.entities.models.calibration import Calibration, Measurement
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.interface_adapters.controllers.calibrations.add_calibration_controller import (
    AddCalibrationController,
)
from src.interface_adapters.presenters.calibration_presenter import CalibrationPresenter
from tests.utils.entity_factories import create_calibration


@pytest.fixture
def mock_add_calibration_use_case() -> AsyncMock:
    return AsyncMock(spec=AddCalibrationUseCase)


@pytest.fixture
def add_calibration_controller(
    mock_add_calibration_use_case: AsyncMock,
) -> AddCalibrationController:
    return AddCalibrationController(
        add_calibration_use_case=mock_add_calibration_use_case
    )


@pytest.fixture
def valid_request() -> CalibrationCreateRequest:
    """Provides a valid calibration creation request."""
    return CalibrationCreateRequest(
        calibration_type="gain",  # Use valid enum string
        value=12.34,
        timestamp="2024-01-01T10:00:00Z",
        username="testuser",
    )


@pytest.fixture
def sample_calibration(valid_request: CalibrationCreateRequest) -> Calibration:
    """Provides a sample Calibration entity based on valid_request."""
    # Use the factory, mapping request fields to factory parameters
    return create_calibration(
        measurement=Measurement(
            value=valid_request.value,
            type=CalibrationType(valid_request.calibration_type),
        ),
        timestamp=Iso8601Timestamp(valid_request.timestamp),
        username=valid_request.username,
        tags=[],  # Default to empty tags for this sample
    )


@pytest.mark.asyncio
async def test_create_calibration_success(
    add_calibration_controller: AddCalibrationController,
    mock_add_calibration_use_case: AsyncMock,
    valid_request: CalibrationCreateRequest,
    sample_calibration: Calibration,
):
    """Test successful calibration creation."""
    # Arrange
    mock_output = AddCalibrationOutput(created_calibration=sample_calibration)
    mock_add_calibration_use_case.return_value = mock_output

    expected_response = CalibrationCreateResponse(calibration_id=sample_calibration.id)

    with patch.object(
        CalibrationPresenter,
        "present_calibration_creation",
        return_value=expected_response,
    ) as mock_presenter:
        # Act
        response = await add_calibration_controller.create_calibration(valid_request)

        # Assert
        mock_add_calibration_use_case.assert_awaited_once()
        call_args = mock_add_calibration_use_case.call_args[0][0]
        assert isinstance(call_args, AddCalibrationInput)
        assert call_args.calibration_type == valid_request.calibration_type
        assert call_args.value == valid_request.value
        assert call_args.timestamp_str == valid_request.timestamp
        assert call_args.username == valid_request.username

        mock_presenter.assert_called_once_with(mock_output)
        assert response == expected_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_type", "expected_exception"),
    [
        (InputParseError("Invalid timestamp"), InputParseError),
        (DatabaseOperationError("DB connection failed"), DatabaseOperationError),
        (UseCaseError("Something went wrong"), UseCaseError),
        (
            ValueError("Unexpected"),
            UseCaseError,
        ),  # Test controller catches generic exceptions
    ],
)
async def test_create_calibration_exceptions(
    add_calibration_controller: AddCalibrationController,
    mock_add_calibration_use_case: AsyncMock,
    valid_request: CalibrationCreateRequest,
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test controller exception handling during calibration creation."""
    # Arrange
    mock_add_calibration_use_case.side_effect = error_type

    # Act & Assert
    with pytest.raises(expected_exception):
        await add_calibration_controller.create_calibration(valid_request)

    mock_add_calibration_use_case.assert_awaited_once()
