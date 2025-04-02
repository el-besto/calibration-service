# tests/unit/use_cases/calibrations/test_list_calibrations.py
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.calibrations.list_calibrations import (
    ListCalibrationsInput,
    ListCalibrationsOutput,
    ListCalibrationsUseCase,
)
from src.entities.exceptions import InputParseError
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from tests.utils.entity_factories import create_calibration


@pytest.fixture
def list_calibrations_use_case(
    mock_calibration_repository: AsyncMock,
) -> ListCalibrationsUseCase:
    """Provides an instance of the ListCalibrationsUseCase."""
    return ListCalibrationsUseCase(calibration_repository=mock_calibration_repository)


@pytest.mark.asyncio
async def test_list_calibrations_success_no_filters(
    list_calibrations_use_case: ListCalibrationsUseCase,
    mock_calibration_repository: AsyncMock,
):
    """Test successful listing with no filters."""
    # Arrange
    mock_calibrations = [create_calibration(), create_calibration()]
    mock_calibration_repository.list_by_filters.return_value = mock_calibrations
    input_data = ListCalibrationsInput()  # No filters

    # Act
    result = await list_calibrations_use_case(input_data)

    # Assert
    assert isinstance(result, ListCalibrationsOutput)
    assert result.calibrations == mock_calibrations
    mock_calibration_repository.list_by_filters.assert_awaited_once_with(
        username=None,
        timestamp=None,
        calibration_type=None,
        tags=None,
    )


@pytest.mark.asyncio
async def test_list_calibrations_success_with_filters(
    list_calibrations_use_case: ListCalibrationsUseCase,
    mock_calibration_repository: AsyncMock,
):
    """Test successful listing with filters."""
    # Arrange
    mock_calibrations = [create_calibration()]  # Assume repo filters correctly
    mock_calibration_repository.list_by_filters.return_value = mock_calibrations

    username_filter = "filter_user"
    timestamp_filter_str = "2024-02-01T10:00:00Z"
    type_filter_str = "gain"

    input_data = ListCalibrationsInput(
        username=username_filter,
        timestamp_str=timestamp_filter_str,
        calibration_type_str=type_filter_str,
    )
    # Expected parsed values after input DTO __post_init__
    expected_timestamp = Iso8601Timestamp(timestamp_filter_str)
    expected_type = CalibrationType(type_filter_str)

    # Act
    result = await list_calibrations_use_case(input_data)

    # Assert
    assert isinstance(result, ListCalibrationsOutput)
    assert result.calibrations == mock_calibrations
    mock_calibration_repository.list_by_filters.assert_awaited_once_with(
        username=username_filter,
        timestamp=expected_timestamp,
        calibration_type=expected_type,
        tags=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("invalid_filter_key", "invalid_value"),
    [
        ("timestamp_str", "invalid-date"),
        ("calibration_type_str", "invalid-type"),
    ],
)
async def test_list_calibrations_input_parse_error(
    list_calibrations_use_case: ListCalibrationsUseCase,  # Not strictly needed, error before call  # pyright: ignore
    mock_calibration_repository: AsyncMock,
    invalid_filter_key: str,
    invalid_value: str,
):
    """Test that invalid filter strings raise InputParseError during DTO creation."""
    # Arrange
    valid_filters = {
        "username": "user",
        "timestamp_str": "2024-01-01T00:00:00Z",
        "calibration_type_str": "gain",
    }
    invalid_filters = {**valid_filters, invalid_filter_key: invalid_value}

    # Act & Assert
    with pytest.raises(InputParseError):
        # Error happens in __post_init__
        # Ignore type error: invalid_filters never contains 'tags' key in this test
        ListCalibrationsInput(**invalid_filters)  # type: ignore[arg-type]

    mock_calibration_repository.list_by_filters.assert_not_awaited()
