from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.entities.models.calibration import Calibration
from src.entities.value_objects.calibration_type import CalibrationType, Measurement
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


class CalibrationCreateInput(BaseModel):
    """Input schema for creating a new calibration."""

    measurement: Measurement
    timestamp: Iso8601Timestamp
    username: str
    tags: list[str] | None = None

    def to_entity(self) -> Calibration:
        """Convert input schema to Calibration entity."""
        return Calibration(
            measurement=self.measurement,
            timestamp=self.timestamp,
            username=self.username,
            tags=[],  # Tags will be added separately
        )


class CalibrationReadResponse(BaseModel):
    """Response schema for reading a single calibration."""

    id: UUID
    value: float
    type: CalibrationType
    timestamp: datetime
    username: str
    tags: list[str]

    model_config = {"from_attributes": True}


class CalibrationTagUpdateInput(BaseModel):
    """Input schema for adding tags to a calibration."""

    tags: list[str]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate that tags are not empty."""
        if not v:
            raise ValueError("Tags cannot be empty")
        return v


# === Request Schemas ===


class CalibrationCreateRequest(BaseModel):
    """Request schema for creating a new calibration."""

    calibration_type: str
    value: float
    timestamp: str = Field(..., description="Timestamp in ISO 8601 format")
    username: str


# === Response Schemas ===


class CalibrationCreateResponse(BaseModel):
    """Response schema after creating a new calibration."""

    calibration_id: UUID


class CalibrationListResponse(BaseModel):
    """Response schema for a list of calibrations."""

    calibrations: list[CalibrationReadResponse]


class CalibrationResponse(BaseModel):
    """Response schema for a single calibration for tag retrieval."""

    calibration_id: UUID = Field(..., alias="id")
    calibration_type: CalibrationType = Field(..., alias="type")
    value: float
    timestamp: Iso8601Timestamp  # Use Iso8601Timestamp for output
    username: str

    model_config = {
        "from_attributes": True,  # Allow creating from entity
        "populate_by_name": True,  # Allow using aliases like 'id' and 'type'
    }
