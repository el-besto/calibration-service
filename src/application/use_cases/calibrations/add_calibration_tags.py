# from ulid import ULID
from uuid import UUID

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.use_cases.exceptions import CalibrationNotFoundError
from src.entities.models.calibration import Calibration
from src.entities.models.calibration_tag_association import CalibrationTagAssociation


class AddCalibrationTagUseCase:
    """Use case for adding tags to an existing calibration.

    This class implements the business logic for adding tags to an existing
    calibration.

    Attributes:
        _calibration_repository: The repository for storing calibrations.
    """

    def __init__(self, calibration_repository: CalibrationRepository) -> None:
        """Initialize the use case.

        Args:
            calibration_repository: The repository for storing calibrations.
        """
        self._calibration_repository = calibration_repository

    async def __call__(
        self,
        calibration_id: UUID,
        calibration_tag_associations: list[CalibrationTagAssociation],
    ) -> Calibration | None:
        """Add tag associations to an existing calibration.

        Args:
            calibration_id: The ID of the calibration to add tags to.
            calibration_tag_associations: The associations to add.

        Returns:
            Calibration: The updated calibration.

        Raises:
            CalibrationNotFoundError: If the calibration is not found.
        """
        # Check if calibration exists
        calibration = await self._calibration_repository.get(id=calibration_id)
        if not calibration:
            raise CalibrationNotFoundError(str(calibration_id))

        # Add tags to calibration
        await self._calibration_repository.add_tags(
            calibration_id=calibration_id,
            calibration_tag_associations=calibration_tag_associations,
        )

        # Return the updated calibration
        return await self._calibration_repository.get(id=calibration_id)
