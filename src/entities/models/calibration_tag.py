from dataclasses import dataclass, field
from datetime import UTC, datetime

# from ulid import ULID
from uuid import UUID, uuid4


@dataclass
class CalibrationTag:
    """
    Represents a calibration tag with archive and modification tracking.

    :ivar name: The name of the calibration tag.
    :type name: str
    :ivar tag_id: Unique identifier of the tag.
    :type tag_id: ULID
    :ivar calibration_id: Identifier associated with the related calibration.
    :type calibration_id: ULID
    :ivar archived_at: Timestamp indicating when the tag was archived, or None
        if the tag is not archived.
    :type archived_at: datetime | None
    :ivar modified_at: Timestamp of the last modification to the tag.
    :type modified_at: datetime
    :ivar created_at: Timestamp of the tag's creation.
    :type created_at: datetime
    :ivar id: Unique identifier automatically generated for this tag instance.
    :type id: ULID
    """

    tag_id: UUID
    calibration_id: UUID
    name: str
    archived_at: datetime | None = None
    modified_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)

    @property
    def is_archived(self) -> bool:
        """Determine if the tag is archived (i.e., `archived_at` is not None)."""
        return self.archived_at is not None

    def _update_modified_at(self):
        """Private method to update the `modified_at` timestamp."""
        self.modified_at = datetime.now(UTC)

    def archive(self):
        """Archive the tag and update the `modified_at` timestamp."""
        if not self.is_archived:
            self.archived_at = datetime.now(UTC)
            self._update_modified_at()

    def restore(self):
        if self.is_archived:
            self.archived_at = None
            self._update_modified_at()
