from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class GetTagsForCalibrationInput:
    """Input DTO for retrieving tags for a specific calibration."""

    calibration_id: UUID
    timestamp: datetime  # Use raw datetime, conversion happens earlier


@dataclass(frozen=True)
class GetTagsForCalibrationOutput:
    """Output DTO for retrieving tags for a specific calibration."""

    tag_names: list[str]
