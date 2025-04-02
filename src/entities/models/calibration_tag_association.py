from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class CalibrationTagAssociation:
    """
    Represents the association between a Calibration and a Tag,
    tracking when the tag association was created and archived.

    Archiving indicates the tag is no longer actively applied to the calibration
    for that specific instance of the association. A new association record
    would be created if the tag is re-applied.

    :ivar tag_id: Unique identifier of the associated Tag.
    :type tag_id: UUID
    :ivar calibration_id: Unique identifier of the associated Calibration.
    :type calibration_id: UUID
    :ivar archived_at: Timestamp indicating when the association was archived,
        or None if the association is active.
    :type archived_at: datetime | None
    :ivar created_at: Timestamp of the association's creation.
    :type created_at: datetime
    :ivar id: Unique identifier automatically generated for this association instance.
    :type id: UUID
    """

    calibration_id: UUID
    tag_id: UUID  # Ensure this links to the Tag entity
    archived_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    @property
    def is_archived(self) -> bool:
        """Determine if the association is archived (i.e., `archived_at` is not None)."""
        return self.archived_at is not None

    def archive(self):
        """Archive the association."""
        if not self.is_archived:
            self.archived_at = datetime.now(UTC)
