from dataclasses import dataclass, field
from uuid import UUID, uuid4

# from ulid import ULID
from src.entities.models.tag import Tag
from src.entities.value_objects.calibration_type import CalibrationType, Measurement
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


@dataclass
class Calibration:
    """
    Represents a calibration performed with specific measurement and metadata.

    This class is used to store calibration data along with its associated
    metadata such as timestamp, tags, and a unique identifier. It ensures that
    all necessary information for calibrations is structured and easily
    accessible.

    :ivar measurement: Represents the measurement associated with the calibration.
    :type measurement: CalibrationType
    :ivar timestamp: ISO 8601 formatted timestamp indicating when the calibration
        was performed.
    :type timestamp: Iso8601Timestamp
    :ivar username: Identifier for the user associated with the calibration. TODO: Change to user_id and link to User entity.
    :type username: str
    :ivar tags: A list of tags associated with the calibration for categorization
        and filtering purposes. Represents the actual Tag entities linked via the association table.
    :type tags: list[Tag]
    :ivar id: A unique identifier automatically generated for the calibration.
    :type id: UUID
    """

    measurement: Measurement
    timestamp: Iso8601Timestamp
    username: str
    tags: list[Tag] = field(default_factory=list)
    # value: float
    # created_at: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)

    @property
    def value(self) -> float:
        """Accessor property for measurement value."""
        return self.measurement.value

    @property
    def type(self) -> CalibrationType:
        """Accessor property for measurement type."""
        return self.measurement.type

    @property
    def tag_names(self) -> list[str]:
        """Accessor property for the names of the associated tags."""
        return [tag.name for tag in self.tags]
