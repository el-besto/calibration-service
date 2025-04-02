from dataclasses import dataclass
from uuid import UUID

from loguru import logger

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.repositories.tag_repository import TagRepository
from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
    ValidationError,
)
from src.entities.models.calibration_tag_association import CalibrationTagAssociation


@dataclass(frozen=True)
class AddBulkTagsToCalibrationInput:
    calibration_id: UUID
    tag_ids: list[UUID]


@dataclass(frozen=True)
class AddBulkTagsToCalibrationOutput:
    added_associations: list[CalibrationTagAssociation]
    skipped_tag_ids: list[UUID]  # IDs requested but already actively associated


class AddBulkTagsToCalibrationUseCase:
    def __init__(
        self,
        calibration_repository: CalibrationRepository,
        tag_repository: TagRepository,
    ):
        self._calibration_repository = calibration_repository
        self._tag_repository = tag_repository

    async def __call__(
        self, input_data: AddBulkTagsToCalibrationInput
    ) -> AddBulkTagsToCalibrationOutput:
        """Executes the use case to associate multiple tags with a calibration.

        1. Validates that the calibration exists.
        2. Validates that all requested tag IDs exist.
        3. Filters out tags already actively associated with the calibration.
        4. Creates new associations for the remaining valid tags.
        5. Persists the new associations using the CalibrationRepository.

        Args:
            input_data: Contains the calibration_id and a list of tag_ids.

        Returns:
            Output containing the list of newly created associations and skipped tag IDs.

        Raises:
            ValidationError: If input list is empty or contains duplicates.
            CalibrationNotFoundError: If the calibration_id does not exist.
            TagNotFoundError: If one or more tag_ids do not exist.
        """
        calibration_id = input_data.calibration_id
        tag_ids_to_add_set = set(input_data.tag_ids)  # Use set for efficiency

        if not tag_ids_to_add_set:
            raise ValidationError("List of tag IDs cannot be empty.")

        calibration = await self._calibration_repository.get(id=calibration_id)
        if not calibration:
            raise CalibrationNotFoundError(
                f"Calibration with id {calibration_id} not found."
            )

        # 2. Check tag existence using bulk method
        found_tags = await self._tag_repository.get_by_ids(list(tag_ids_to_add_set))
        found_tag_ids = {tag.id for tag in found_tags}

        not_found_ids = tag_ids_to_add_set - found_tag_ids
        if not_found_ids:
            raise TagNotFoundError(
                f"Tags not found: {', '.join(map(str, not_found_ids))}"
            )

        # 3. Filter out already active tags
        current_associations = (
            await self._calibration_repository.get_tag_associations_for_calibration(
                calibration_id
            )
        )
        active_tag_ids = {
            assoc.tag_id for assoc in current_associations if not assoc.is_archived
        }

        new_tag_ids_to_associate = list(tag_ids_to_add_set - active_tag_ids)
        skipped_tag_ids = list(tag_ids_to_add_set.intersection(active_tag_ids))

        if not new_tag_ids_to_associate:
            logger.info(
                f"No new tags to associate for calibration {calibration_id}. All requested tags already active."
            )
            return AddBulkTagsToCalibrationOutput(
                added_associations=[], skipped_tag_ids=skipped_tag_ids
            )

        # 4. Create new association entities
        new_associations = [
            CalibrationTagAssociation(calibration_id=calibration_id, tag_id=tag_id)
            for tag_id in new_tag_ids_to_associate
        ]

        # 5. Add using the repository
        # This raises DatabaseOperationError on failure
        await self._calibration_repository.add_tags(
            calibration_id=calibration_id, calibration_tag_associations=new_associations
        )

        logger.info(
            f"Added {len(new_associations)} new tag associations for calibration {calibration_id}."
        )

        # Return the list of associations we *intended* to add (now persisted)
        return AddBulkTagsToCalibrationOutput(
            added_associations=new_associations, skipped_tag_ids=skipped_tag_ids
        )
