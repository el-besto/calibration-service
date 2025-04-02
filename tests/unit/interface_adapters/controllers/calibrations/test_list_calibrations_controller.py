from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from src.application.use_cases.calibrations.list_calibrations import (
    ListCalibrationsInput,
    ListCalibrationsOutput,
    ListCalibrationsUseCase,
)
from src.application.use_cases.exceptions import UseCaseError
from src.drivers.rest.schemas.calibration_schemas import (
    CalibrationListResponse,
    CalibrationReadResponse,
)
from src.entities.exceptions import DatabaseOperationError, InputParseError
from src.entities.models.calibration import Calibration, Measurement
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.interface_adapters.controllers.calibrations.list_calibrations_controller import (
    ListCalibrationsController,
)
from tests.utils.entity_factories import create_calibration


@pytest.fixture
def mock_list_calibrations_use_case() -> AsyncMock:
    return AsyncMock(spec=ListCalibrationsUseCase)


@pytest.fixture
def list_calibrations_controller(
    mock_list_calibrations_use_case: AsyncMock,
) -> ListCalibrationsController:
    return ListCalibrationsController(
        list_calibrations_use_case=mock_list_calibrations_use_case
    )


@pytest.fixture
def sample_calibrations_list() -> list[Calibration]:
    # Use the factory function to create sample calibrations
    cal1 = create_calibration(
        measurement=Measurement(value=25.5, type=CalibrationType.gain),
        timestamp=Iso8601Timestamp("2023-10-26T10:00:00Z"),
        username="testuser",
        # Override default ID if needed for specific tests, otherwise use consistent default
        calibration_id=UUID("00000000-0000-0000-0000-000000000001"),
    )
    cal2 = create_calibration(
        measurement=Measurement(value=45.0, type=CalibrationType.temp),
        timestamp=Iso8601Timestamp("2023-10-26T10:05:00Z"),
        username="testuser",
        calibration_id=UUID("00000000-0000-0000-0000-000000000002"),
    )
    return [cal1, cal2]


@pytest.mark.asyncio
@patch(
    "src.interface_adapters.controllers.calibrations.list_calibrations_controller.CalibrationPresenter.present_list_output"
)
async def test_list_calibrations_success_no_filters(
    mock_presenter: MagicMock,
    list_calibrations_controller: ListCalibrationsController,
    mock_list_calibrations_use_case: AsyncMock,
    sample_calibrations_list: list[Calibration],
):
    """Test successful listing of calibrations with no filters."""
    # Arrange
    mock_output = ListCalibrationsOutput(calibrations=sample_calibrations_list)
    mock_list_calibrations_use_case.return_value = mock_output

    # Prepare expected presenter output (Pydantic model)
    expected_response = CalibrationListResponse(
        calibrations=[
            CalibrationReadResponse(
                id=cal.id,
                type=cal.measurement.type,
                value=cal.measurement.value,
                timestamp=cal.timestamp.to_datetime(),
                username=cal.username,
                tags=[],
            )
            for cal in sample_calibrations_list
        ]
    )
    mock_presenter.return_value = expected_response

    # Act
    response = await list_calibrations_controller.list_calibrations()  # No filters

    # Assert
    mock_list_calibrations_use_case.assert_awaited_once()
    # Check input DTO passed to use case (should have None for filters)
    call_args = mock_list_calibrations_use_case.call_args[0][0]
    assert isinstance(call_args, ListCalibrationsInput)
    assert call_args.username is None
    assert call_args.timestamp_str is None
    assert call_args.calibration_type_str is None

    mock_presenter.assert_called_once_with(mock_output)
    assert response == expected_response


@pytest.mark.asyncio
@patch(
    "src.interface_adapters.controllers.calibrations.list_calibrations_controller.CalibrationPresenter.present_list_output"
)
async def test_list_calibrations_success_with_filters(
    mock_presenter: MagicMock,
    list_calibrations_controller: ListCalibrationsController,
    mock_list_calibrations_use_case: AsyncMock,
    sample_calibrations_list: list[Calibration],
):
    """Test successful listing of calibrations with filters."""
    # Arrange
    # Assume the use case correctly filters, returning only the first sample
    mock_output = ListCalibrationsOutput(calibrations=[sample_calibrations_list[0]])
    mock_list_calibrations_use_case.return_value = mock_output

    filters = {
        "username": "testuser",
        "timestamp": "2023-10-26T10:00:00Z",
        "calibration_type": "gain",
        "tags": ["rick"],
    }

    # Prepare expected presenter output (Pydantic model)
    cal = sample_calibrations_list[0]
    expected_response = CalibrationListResponse(
        calibrations=[
            CalibrationReadResponse(
                id=cal.id,
                type=cal.measurement.type,
                value=cal.measurement.value,
                timestamp=cal.timestamp.to_datetime(),
                username=cal.username,
                tags=[],
            )
        ]
    )
    mock_presenter.return_value = expected_response

    # Act
    response = await list_calibrations_controller.list_calibrations(**filters)

    # Assert
    mock_list_calibrations_use_case.assert_awaited_once()
    # Check input DTO passed to use case
    call_args = mock_list_calibrations_use_case.call_args[0][0]
    assert isinstance(call_args, ListCalibrationsInput)
    assert call_args.username == filters["username"]
    assert call_args.timestamp_str == filters["timestamp"]
    assert call_args.calibration_type_str == filters["calibration_type"]

    mock_presenter.assert_called_once_with(mock_output)
    assert response == expected_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filters", "error_type", "expected_exception"),
    [
        (
            {"timestamp": "invalid-date"},
            InputParseError("Simulated invalid date"),
            InputParseError,
        ),  # Simulate input parse error during DTO creation
        (
            {},
            DatabaseOperationError("Connection failed"),
            DatabaseOperationError,
        ),  # Simulate DB error from use case
        (
            {},
            UseCaseError("Internal logic error"),
            UseCaseError,
        ),  # Simulate generic use case error
        (
            {},
            ValueError("Unexpected"),
            UseCaseError,
        ),  # Simulate unexpected error from use case
    ],
)
async def test_list_calibrations_exceptions(
    list_calibrations_controller: ListCalibrationsController,
    mock_list_calibrations_use_case: AsyncMock,
    filters: dict[str, str | None],
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test controller exception handling during listing calibrations."""
    # Arrange
    if not isinstance(error_type, InputParseError):
        mock_list_calibrations_use_case.side_effect = error_type

    # Act & Assert
    with pytest.raises(expected_exception):
        # InputParseError is raised during DTO __post_init__ within the controller method
        await list_calibrations_controller.list_calibrations(**filters)

    # Check mock calls based on expected error origin
    if isinstance(error_type, InputParseError):
        mock_list_calibrations_use_case.assert_not_awaited()
    else:
        mock_list_calibrations_use_case.assert_awaited_once()
