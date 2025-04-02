from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Tag:
    """
    Represents a tag that can be associated with calibrations.

    :ivar name: The name of the tag.
    :type name: str
    :ivar created_at: Timestamp of the tag's creation.
    :type created_at: datetime
    :ivar id: Unique identifier automatically generated for this tag instance.
    :type id: UUID
    """

    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)
