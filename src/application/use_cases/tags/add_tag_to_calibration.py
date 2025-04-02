from dataclasses import dataclass
from uuid import UUID

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.repositories.tag_repository import TagRepository
from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
)
from src.entities.models.calibration_tag_association import CalibrationTagAssociation


@dataclass(frozen=True)
class AddTagToCalibrationInput:
    calibration_id: UUID
    tag_id: UUID


@dataclass(frozen=True)
class AddTagToCalibrationOutput:
    association: CalibrationTagAssociation


class AddTagToCalibrationUseCase:
    def __init__(
        self,
        calibration_repository: CalibrationRepository,
        tag_repository: TagRepository,
    ):
        self._calibration_repository = calibration_repository
        self._tag_repository = tag_repository

    async def execute(
        self, input_data: AddTagToCalibrationInput
    ) -> AddTagToCalibrationOutput:
        """Executes the use case to associate a tag with a calibration.

        1. Validates that the calibration exists.
        2. Validates that the tag exists.
        3. Checks for an existing *active* association for this pair.
           - If an active association exists, return it.
           - If an *inactive* (archived) association exists, create a new one.
           - If no association exists, create a new one.
        4. Creates a new CalibrationTagAssociation entity.
        5. Uses the CalibrationRepository to persist the new association.

        Args:
            input_data: Contains the calibration_id and tag_id.

        Returns:
            Output containing the created or existing active association.

        Raises:
            CalibrationNotFoundError: If the calibration_id does not exist.
            TagNotFoundError: If the tag_id does not exist.
            DatabaseOperationError: If the association cannot be saved.
        """
        # Validate input IDs
        if not input_data.calibration_id or not input_data.tag_id:
            raise ValueError("Calibration ID and Tag ID must be provided.")

        # 1. Check if calibration exists
        calibration = await self._calibration_repository.get(
            id=input_data.calibration_id
        )
        if not calibration:
            raise CalibrationNotFoundError(
                f"Calibration with id {input_data.calibration_id} not found."
            )

        # 2. Check if tag exists
        tag = await self._tag_repository.get_by_id(input_data.tag_id)
        if not tag:
            raise TagNotFoundError(f"Tag with id {input_data.tag_id} not found.")

        # 3. Check for existing active associations
        existing_associations = (
            await self._calibration_repository.get_tag_associations_for_calibration(
                calibration_id=input_data.calibration_id
            )
        )
        active_association = None
        for assoc in existing_associations:
            if assoc.tag_id == input_data.tag_id and not assoc.is_archived:
                active_association = assoc
                break
        if active_association:
            return AddTagToCalibrationOutput(association=active_association)

        # 4. Create a new association entity
        new_association = CalibrationTagAssociation(
            calibration_id=input_data.calibration_id, tag_id=input_data.tag_id
        )

        # 5. Add the single new association using the repository method.
        # The repository now raises DatabaseOperationError on failure.
        await self._calibration_repository.add_tags(
            calibration_id=input_data.calibration_id,
            calibration_tag_associations=[new_association],
        )
        # If add_tags succeeds, return the association we intended to add.
        return AddTagToCalibrationOutput(association=new_association)
