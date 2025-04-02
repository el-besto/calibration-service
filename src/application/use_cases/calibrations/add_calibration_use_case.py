from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.application.repositories.calibration_repository import CalibrationRepository
from src.entities.exceptions import (
    DatabaseOperationError,
    InputParseError,
)
from src.entities.models.calibration import Calibration, Measurement
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


@dataclass(frozen=True)
class AddCalibrationInput:
    calibration_type: str
    value: float
    timestamp_str: str | None  # Changed type hint to optional
    username: str
    # Optionally allow providing an ID, otherwise generate one
    id: UUID | None = None


@dataclass(frozen=True)
class AddCalibrationOutput:
    created_calibration: Calibration


class AddCalibrationUseCase:
    """Use case for adding a new calibration to the system.

    This class implements the business logic for creating and storing
    new calibrations.

    Attributes:
        _calibration_repository: The repository for storing calibrations.
    """

    def __init__(self, calibration_repository: CalibrationRepository) -> None:
        """Initialize the use case.

        Args:
            calibration_repository: The repository for storing calibrations.
        """
        self._calibration_repository = calibration_repository

    async def __call__(self, input_data: AddCalibrationInput) -> AddCalibrationOutput:
        """Add a new calibration to the system based on input data."""
        # Generate ID if not provided
        calibration_id = input_data.id if input_data.id is not None else uuid4()

        # Validate and create value objects
        try:
            measurement = Measurement(
                value=input_data.value,
                type=CalibrationType(input_data.calibration_type),
            )
            # Handle optional timestamp
            if input_data.timestamp_str is None:
                timestamp_to_parse = datetime.now(UTC).isoformat()  # Default to now
            else:
                timestamp_to_parse = input_data.timestamp_str  # Use provided value

            timestamp = Iso8601Timestamp(
                timestamp_to_parse
            )  # Parse the determined string
        except (ValueError, TypeError) as e:
            # Catch errors from Enum creation or Iso8601Timestamp validation
            raise InputParseError(f"Invalid input data: {e}") from e

        # Create Calibration entity
        calibration = Calibration(
            id=calibration_id,
            measurement=measurement,
            timestamp=timestamp,
            username=input_data.username,
            tags=[],  # New calibrations have no tags initially
        )

        # Add the calibration entity to the repository
        try:
            added_calibration = await self._calibration_repository.add_calibration(
                calibration
            )
        except Exception as e:
            # Catch any other exceptions that might occur during the add operation
            raise DatabaseOperationError(
                message="Failed to add calibration to repository",
            ) from e

        return AddCalibrationOutput(created_calibration=added_calibration)
