from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.application.dtos.get_calibrations_by_tag_dtos import (
    GetCalibrationsByTagInput,
    GetCalibrationsByTagOutput,
)
from src.application.use_cases.exceptions import TagNotFoundError, UseCaseError
from src.application.use_cases.tags.get_calibrations_by_tag import (
    GetCalibrationsByTagUseCase,
)
from src.drivers.rest.schemas.calibration_schemas import CalibrationReadResponse
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.entities.models.calibration import (  # For creating sample data
    Calibration,
    Measurement,
)
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.interface_adapters.controllers.tags.get_calibrations_by_tag_controller import (
    GetCalibrationsByTagController,
)
from src.interface_adapters.presenters.calibration_presenter import CalibrationPresenter


@pytest.fixture
def mock_get_calibrations_use_case() -> AsyncMock:
    return AsyncMock(spec=GetCalibrationsByTagUseCase)


@pytest.fixture
def get_calibrations_controller(
    mock_get_calibrations_use_case: AsyncMock,
) -> GetCalibrationsByTagController:
    return GetCalibrationsByTagController(
        get_calibrations_by_tag_use_case=mock_get_calibrations_use_case
    )


@pytest.fixture
def sample_tag_name() -> str:
    return "target-tag"


@pytest.fixture
def sample_timestamp() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def sample_username() -> str:
    return "test-user"


@pytest.fixture
def sample_calibrations_list() -> list[Calibration]:
    # Helper to create a list of sample Calibrations for use case output
    return [
        Calibration(
            id=uuid4(),
            measurement=Measurement(value=30.0, type=CalibrationType.offset),
            timestamp=Iso8601Timestamp("2023-10-27T11:00:00Z"),
            username="test-user",
            tags=[],  # Tags list within calibration itself might not be populated here
        ),
        Calibration(
            id=uuid4(),
            measurement=Measurement(value=50.0, type=CalibrationType.gain),
            timestamp=Iso8601Timestamp("2023-10-27T11:05:00Z"),
            username="test-user",
            tags=[],
        ),
    ]


@pytest.fixture
def expected_success_response(
    sample_calibrations_list: list[Calibration],
) -> list[CalibrationReadResponse]:
    # Assume presenter formats correctly
    return [
        CalibrationReadResponse(
            calibration_id=cal.id,
            calibration_type=cal.measurement.type,
            value=cal.measurement.value,
            timestamp=cal.timestamp.to_datetime(),
            username=cal.username,
            tags=[tag.name for tag in cal.tags],
        )
        for cal in sample_calibrations_list
    ]


# --- Test Cases ---


@pytest.mark.asyncio
async def test_get_calibrations_by_tag_success(
    get_calibrations_controller: GetCalibrationsByTagController,
    mock_get_calibrations_use_case: AsyncMock,
    sample_tag_name: str,
    sample_timestamp: datetime,
    sample_username: str,
    sample_calibrations_list: list[Calibration],
    expected_success_response: list[CalibrationReadResponse],
):
    """Test successful retrieval of calibrations by tag."""
    # Arrange
    mock_output = GetCalibrationsByTagOutput(calibrations=sample_calibrations_list)
    mock_get_calibrations_use_case.execute.return_value = mock_output

    with patch.object(
        CalibrationPresenter,
        "present_calibration_list",
        return_value=expected_success_response,
    ) as mock_presenter:
        # Act
        response = await get_calibrations_controller.get_calibrations_by_tag(
            tag_name=sample_tag_name,
            timestamp=sample_timestamp,
            username=sample_username,
        )

        # Assert
        mock_get_calibrations_use_case.execute.assert_awaited_once()
        # Check input DTO passed to use case
        call_args = mock_get_calibrations_use_case.execute.call_args[0][0]
        assert isinstance(call_args, GetCalibrationsByTagInput)
        assert call_args.tag_name == sample_tag_name
        assert call_args.timestamp == sample_timestamp
        assert call_args.username == sample_username

        mock_presenter.assert_called_once_with(sample_calibrations_list)
        assert response == expected_success_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_type", "expected_exception"),
    [
        (TagNotFoundError("Tag 'target-tag' not found"), NotFoundError),
        (DatabaseOperationError("DB connection failed"), DatabaseOperationError),
        (UseCaseError("Internal logic error"), UseCaseError),
        (Exception("Completely unexpected"), UseCaseError),
    ],
)
async def test_get_calibrations_by_tag_exceptions(
    get_calibrations_controller: GetCalibrationsByTagController,
    mock_get_calibrations_use_case: AsyncMock,
    sample_tag_name: str,
    sample_timestamp: datetime,
    sample_username: str,
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test controller exception handling during retrieval."""
    # Arrange
    mock_get_calibrations_use_case.execute.side_effect = error_type

    # Act & Assert
    with pytest.raises(expected_exception):
        await get_calibrations_controller.get_calibrations_by_tag(
            tag_name=sample_tag_name,
            timestamp=sample_timestamp,
            username=sample_username,
        )

    # Assert use case was called
    mock_get_calibrations_use_case.execute.assert_awaited_once()
    call_args = mock_get_calibrations_use_case.execute.call_args[0][0]
    assert isinstance(call_args, GetCalibrationsByTagInput)
    assert call_args.tag_name == sample_tag_name
    assert call_args.timestamp == sample_timestamp
    assert call_args.username == sample_username
