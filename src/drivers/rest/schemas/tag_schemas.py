from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# === Request Schemas ===


class TagCreateRequest(BaseModel):
    """Request schema for creating a new tag."""

    name: str


class BulkAddTagsRequest(BaseModel):
    """Request schema for bulk adding tags to a calibration."""

    tag_ids: list[UUID]


class TagOperationRequest(BaseModel):
    """Request schema for adding/removing a tag by name."""

    tag: str  # The name of the tag


# Note: The paths for adding/removing tags often include IDs in the path itself,
# so the request body might be empty or contain other info if needed.
# Let's assume for now path parameters are used, so no specific request body schemas
# are needed for add/remove beyond potentially validation.


# === Response Schemas ===


class TagResponse(BaseModel):
    """Response schema for a single tag."""

    id: UUID
    name: str

    # Allow conversion from ORM or other objects
    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    """Response schema for a list of tags."""

    tags: list[TagResponse]


class AssociationResponse(BaseModel):
    """Response schema for a calibration-tag association."""

    id: UUID
    calibration_id: UUID
    tag_id: UUID
    created_at: datetime
    archived_at: datetime | None = None

    model_config = {"from_attributes": True}


class BulkAddTagsResponse(BaseModel):
    """Response schema for bulk adding tags."""

    added_associations: list[AssociationResponse]
    skipped_tag_ids: list[UUID]


class TagOperationResponse(BaseModel):
    """Generic success response for tag operations."""

    message: str
