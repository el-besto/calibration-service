"""Test the add calibration use case."""

from typing import TYPE_CHECKING
from uuid import UUID

import pytest

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.use_cases.calibrations.add_calibration_use_case import (
    AddCalibrationInput,
    AddCalibrationUseCase,
)
from src.entities.exceptions import DatabaseOperationError, InputParseError
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.infrastructure.repositories.calibration_repository.in_memory_repository import (
    InMemoryCalibrationRepository,
)

if TYPE_CHECKING:
    from src.application.use_cases.calibrations.add_calibration_use_case import (
        AddCalibrationOutput,
    )


@pytest.fixture
def calibration_repository() -> CalibrationRepository:
    # Clear mock repo before each test
    repo = InMemoryCalibrationRepository()
    repo.clear()
    return repo


@pytest.fixture
def add_calibration_use_case(
    calibration_repository: CalibrationRepository,
) -> AddCalibrationUseCase:
    return AddCalibrationUseCase(calibration_repository)


@pytest.mark.asyncio
async def test_add_existing_calibration_id_raises_error(
    calibration_repository: InMemoryCalibrationRepository,
    add_calibration_use_case: AddCalibrationUseCase,
):
    """Test adding a calibration with an explicitly provided, existing ID raises DatabaseOperationError."""
    # ARRANGE
    initial_input = AddCalibrationInput(
        calibration_type="gain",
        value=1.0,
        timestamp_str="2023-01-01T10:00:00Z",
        username="user1",
    )
    initial_output = await add_calibration_use_case(initial_input)
    existing_id = initial_output.created_calibration.id
    duplicate_input = AddCalibrationInput(
        id=existing_id,
        calibration_type="offset",
        value=2.0,
        timestamp_str="2023-01-01T11:00:00Z",
        username="user2",
    )
    # ACT & ASSERT
    with pytest.raises(DatabaseOperationError, match="Calibration already exists"):
        await add_calibration_use_case(duplicate_input)


@pytest.mark.asyncio
async def test_calibration_successfully_created_with_valid_input(
    add_calibration_use_case: AddCalibrationUseCase,
):
    """Test that a calibration is successfully created with valid input data."""
    # ARRANGE
    input_timestamp = "2023-01-01T12:00:00Z"
    input_data = AddCalibrationInput(
        calibration_type="gain",
        value=1.0,
        timestamp_str=input_timestamp,
        username="test_user",
    )

    # ACT
    result_output: AddCalibrationOutput = await add_calibration_use_case(input_data)
    result_calibration = result_output.created_calibration

    # ASSERT
    assert result_calibration is not None
    assert isinstance(result_calibration.id, UUID)
    assert result_calibration.measurement.value == 1.0
    assert result_calibration.measurement.type == CalibrationType.gain
    assert len(result_calibration.tags) == 0
    assert result_calibration.username == "test_user"
    assert isinstance(result_calibration.timestamp, Iso8601Timestamp)
    assert result_calibration.timestamp.value == input_timestamp


@pytest.mark.asyncio
async def test_add_calibration_invalid_type_raises_error(
    add_calibration_use_case: AddCalibrationUseCase,
):
    """Test that providing an invalid calibration_type raises InputParseError."""
    # ARRANGE
    input_data = AddCalibrationInput(
        calibration_type="invalid_type",
        value=1.0,
        timestamp_str="2023-01-01T12:00:00Z",
        username="test_user",
    )

    # ACT & ASSERT
    with pytest.raises(InputParseError, match="Invalid input data: 'invalid_type'"):
        await add_calibration_use_case(input_data)


@pytest.mark.asyncio
async def test_add_calibration_invalid_timestamp_raises_error(
    add_calibration_use_case: AddCalibrationUseCase,
):
    """Test that providing an invalid timestamp format raises InputParseError."""
    # ARRANGE
    input_data = AddCalibrationInput(
        calibration_type="gain",
        value=1.0,
        timestamp_str="not-a-timestamp",
        username="test_user",
    )

    # ACT & ASSERT
    with pytest.raises(
        InputParseError,
        match="Invalid input data: Invalid ISO 8601 timestamp: not-a-timestamp",
    ):
        await add_calibration_use_case(input_data)
