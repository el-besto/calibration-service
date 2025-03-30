from dataclasses import dataclass, field

# from uuid import UUID
from loguru import logger

from src.application.repositories.calibration_repository import CalibrationRepository
from src.entities.exceptions import InputParseError
from src.entities.models.calibration import Calibration
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


@dataclass(frozen=True)
class ListCalibrationsInput:
    """Input DTO for listing calibrations with optional filters."""

    username: str | None = None
    timestamp_str: str | None = None  # Filter by exact timestamp string for now
    calibration_type_str: str | None = None  # Filter by type string
    tags: list[str] | None = None  # Filter by tag names

    # Parsed value objects (internal use)
    timestamp: Iso8601Timestamp | None = field(init=False, default=None)
    calibration_type: CalibrationType | None = field(init=False, default=None)

    def __post_init__(self):
        """Validate and parse filter strings into value objects."""
        try:
            if self.timestamp_str:
                # Use object.__setattr__ because the dataclass is frozen
                object.__setattr__(
                    self, "timestamp", Iso8601Timestamp(self.timestamp_str)
                )
            if self.calibration_type_str:
                object.__setattr__(
                    self, "calibration_type", CalibrationType(self.calibration_type_str)
                )
        except (ValueError, TypeError) as e:
            raise InputParseError(f"Invalid filter value: {e}") from e


@dataclass(frozen=True)
class ListCalibrationsOutput:
    """Output DTO containing the list of matching calibrations."""

    calibrations: list[Calibration]


class ListCalibrationsUseCase:
    """Use case for listing calibrations based on optional filters."""

    def __init__(self, calibration_repository: CalibrationRepository):
        self._calibration_repository = calibration_repository

    async def __call__(
        self, input_data: ListCalibrationsInput
    ) -> ListCalibrationsOutput:
        """Executes the use case to list calibrations."""
        logger.info(f"Listing calibrations with filters: {input_data}")

        # Pass validated filters to the repository
        calibrations = await self._calibration_repository.list_by_filters(
            username=input_data.username,
            timestamp=input_data.timestamp,  # Pass the parsed value object
            calibration_type=input_data.calibration_type,  # Pass the parsed enum
            tags=input_data.tags,  # Pass the tags list
        )

        logger.info(f"Found {len(calibrations)} calibrations matching filters.")
        return ListCalibrationsOutput(calibrations=calibrations)
