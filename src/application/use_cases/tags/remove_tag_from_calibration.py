from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.repositories.tag_repository import TagRepository
from src.application.use_cases.exceptions import (
    AssociationNotFoundError,
    CalibrationNotFoundError,
    TagNotFoundError,
)
from src.entities.models.calibration_tag_association import CalibrationTagAssociation


@dataclass(frozen=True)
class RemoveTagFromCalibrationInput:
    calibration_id: UUID
    tag_id: UUID


@dataclass(frozen=True)
class RemoveTagFromCalibrationOutput:
    archived_association: CalibrationTagAssociation


class RemoveTagFromCalibrationUseCase:
    def __init__(
        self,
        calibration_repository: CalibrationRepository,
        tag_repository: TagRepository,
    ):
        self._calibration_repository = calibration_repository
        self._tag_repository = tag_repository

    async def execute(
        self, input_data: RemoveTagFromCalibrationInput
    ) -> RemoveTagFromCalibrationOutput:
        """Executes the use case to disassociate a tag from a calibration (by archiving).

        1. Validates that the calibration exists.
        2. Validates that the tag exists.
        3. Finds the *active* (non-archived) association for this pair.
        4. If no active association found, raise AssociationNotFoundError.
        5. Calls the `archive()` method on the found association entity.
        6. Uses the CalibrationRepository's `update_tag_association` method to persist.

        Args:
            input_data: Contains the calibration_id and tag_id.

        Returns:
            Output containing the archived association.

        Raises:
            CalibrationNotFoundError: If the calibration_id does not exist.
            TagNotFoundError: If the tag_id does not exist.
            AssociationNotFoundError: If no *active* association is found for the pair.
        """
        # Validate input IDs
        if not input_data.calibration_id or not input_data.tag_id:
            raise ValueError("Calibration ID and Tag ID must be provided.")

        # 1. Check if calibration exists (optional but good practice)
        calibration = await self._calibration_repository.get(
            id=input_data.calibration_id
        )
        if not calibration:
            raise CalibrationNotFoundError(
                f"Calibration with id {input_data.calibration_id} not found."
            )

        # 2. Check if tag exists (optional but good practice)
        tag = await self._tag_repository.get_by_id(input_data.tag_id)
        if not tag:
            raise TagNotFoundError(f"Tag with id {input_data.tag_id} not found.")

        # 3. Find the active association
        # We need associations active *now* to archive them
        now = datetime.now(UTC)
        active_associations = (
            await self._calibration_repository.get_tag_associations_for_calibration(
                calibration_id=input_data.calibration_id,
                active_at=now,  # Find associations active right now
            )
        )

        association_to_archive = None
        for assoc in active_associations:
            # Double-check the tag ID matches and it's indeed not archived
            if assoc.tag_id == input_data.tag_id and not assoc.is_archived:
                association_to_archive = assoc
                break

        # 4. If no active association found
        if not association_to_archive:
            raise AssociationNotFoundError(
                f"No active association found for calibration {input_data.calibration_id} "
                f"and tag {input_data.tag_id}."
            )

        # 5. Archive the entity
        association_to_archive.archive()  # This sets archived_at = now(UTC)

        # 6. Persist the change using the repository
        updated_association = await self._calibration_repository.update_tag_association(
            association_to_archive
        )

        if not updated_association:
            # This could happen if the association was deleted/archived between steps 3 and 6 (race condition)
            # Or if the update method failed.
            raise RuntimeError(
                f"Failed to update/archive association {association_to_archive.id}. "
                "It might have been modified or deleted concurrently."
            )

        return RemoveTagFromCalibrationOutput(archived_association=updated_association)
