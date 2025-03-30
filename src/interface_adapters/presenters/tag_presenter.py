from src.application.use_cases.tags.add_bulk_tags_to_calibration import (
    AddBulkTagsToCalibrationOutput,
)
from src.drivers.rest.schemas.tag_schemas import (
    AssociationResponse,
    BulkAddTagsResponse,
    TagListResponse,
    TagOperationResponse,
    TagResponse,
)
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.models.tag import Tag


class TagPresenter:
    """Presenter for converting tag/association entities to response schemas."""

    @staticmethod
    def present_tag(entity: Tag) -> TagResponse:
        """Convert a single Tag entity to a TagResponse schema."""
        # Pydantic model_validate handles conversion including UUID to UUID
        return TagResponse.model_validate(entity)

    @staticmethod
    def present_tag_list(entities: list[Tag]) -> TagListResponse:
        """Convert a list of Tag entities to a TagListResponse schema."""
        tag_responses = [TagPresenter.present_tag(tag) for tag in entities]
        return TagListResponse(tags=tag_responses)

    @staticmethod
    def present_association(entity: CalibrationTagAssociation) -> AssociationResponse:
        """Convert a CalibrationTagAssociation entity to an AssociationResponse schema."""
        # Pydantic model_validate handles conversion including UUIDs and datetimes
        return AssociationResponse.model_validate(entity)

    @staticmethod
    def present_bulk_add_output(
        output_dto: AddBulkTagsToCalibrationOutput,
    ) -> BulkAddTagsResponse:
        """Convert the bulk add use case output to a response schema."""
        added_responses = [
            TagPresenter.present_association(assoc)
            for assoc in output_dto.added_associations
        ]
        return BulkAddTagsResponse(
            added_associations=added_responses,
            skipped_tag_ids=output_dto.skipped_tag_ids,
        )

    @staticmethod
    def present_tag_added() -> TagOperationResponse:
        """Returns the standard success response for adding a tag."""
        return TagOperationResponse(message="Tag added successfully")

    @staticmethod
    def present_tag_removed() -> TagOperationResponse:
        """Returns the standard success response for removing a tag."""
        return TagOperationResponse(message="Tag removed successfully")
