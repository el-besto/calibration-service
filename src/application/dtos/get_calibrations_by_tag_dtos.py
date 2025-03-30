from dataclasses import dataclass
from datetime import datetime

from src.entities.models.calibration import Calibration


@dataclass(frozen=True)
class GetCalibrationsByTagInput:
    """Input DTO for retrieving calibrations by tag."""

    tag_name: str
    timestamp: datetime  # Use raw datetime here, conversion happens earlier
    username: str | None


@dataclass(frozen=True)
class GetCalibrationsByTagOutput:
    """Output DTO for retrieving calibrations by tag."""

    calibrations: list[Calibration]
