"""Entity factory utilities for testing."""

from datetime import datetime
from uuid import UUID

from src.entities.models.calibration import Calibration, Measurement
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.models.tag import Tag  # Import base Tag model
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


def create_tag(
    tag_id: UUID | None = None,
    name: str = "default_factory_tag",
) -> Tag:
    """Create a test Tag with default or provided values."""
    if tag_id is None:
        # Use a consistent default UUID for predictability
        tag_id = UUID("22222222-2222-2222-2222-222222222222")
    return Tag(id=tag_id, name=name)


def create_calibration_tag_association(
    association_id: UUID | None = None,
    calibration_id: UUID | None = None,
    tag_id: UUID | None = None,
    created_at: datetime | None = None,
    archived_at: datetime | None = None,
) -> CalibrationTagAssociation:
    """Create a test CalibrationTagAssociation with default/provided values."""
    if association_id is None:
        association_id = UUID("55555555-5555-5555-5555-555555555555")
    if calibration_id is None:
        calibration_id = UUID(
            "11111111-1111-1111-1111-111111111111"
        )  # Match default cal ID
    if tag_id is None:
        tag_id = UUID("22222222-2222-2222-2222-222222222222")  # Match default tag ID
    if created_at is None:
        created_at = datetime.fromisoformat("2024-01-01T10:00:00+00:00")

    return CalibrationTagAssociation(
        id=association_id,
        calibration_id=calibration_id,
        tag_id=tag_id,
        created_at=created_at,
        archived_at=archived_at,
    )


def create_calibration(
    calibration_id: UUID | None = None,
    measurement: Measurement | None = None,
    timestamp: Iso8601Timestamp | None = None,
    username: str = "test_user",
    tags: list[Tag] | None = None,  # Corrected type hint
) -> Calibration:
    """Create a test calibration with default values.

    Args:
        calibration_id: Optional UUID for the calibration. If None, a default UUID is used.
        measurement: Optional measurement. If None, a default gain measurement is created.
        timestamp: Optional timestamp. If None, current UTC time is used.
        username: Username for the calibration. Defaults to "test_user".
        tags: Optional list of tags. If None, an empty list is used.

    Returns:
        Calibration: A test calibration instance.
    """
    if calibration_id is None:
        # Use a consistent default UUID for predictability in tests
        calibration_id = UUID("11111111-1111-1111-1111-111111111111")

    if measurement is None:
        measurement = Measurement(
            value=0.23,
            type=CalibrationType.gain,
        )

    if timestamp is None:
        # Create a consistent timestamp for predictability
        # Using a fixed string makes comparison easier than datetime.now()
        timestamp = Iso8601Timestamp("2024-01-01T12:00:00Z")

    if tags is None:
        tags = []

    return Calibration(
        id=calibration_id,
        measurement=measurement,
        timestamp=timestamp,
        username=username,
        tags=tags,  # Now matches expected type
    )
