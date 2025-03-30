from loguru import logger

from src.application.dtos.get_tags_for_calibration_dtos import (
    GetTagsForCalibrationInput,
    GetTagsForCalibrationOutput,
)
from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.repositories.tag_repository import (
    TagRepository,
)
from src.application.use_cases.exceptions import CalibrationNotFoundError


class GetTagsForCalibrationUseCase:
    """Use case to retrieve tags associated with a specific calibration at a given time."""

    def __init__(
        self,
        calibration_repository: CalibrationRepository,
        tag_repository: TagRepository,
    ) -> None:
        self._calibration_repo = calibration_repository
        self._tag_repo = tag_repository  # Store tag repo

    async def execute(
        self, input_dto: GetTagsForCalibrationInput
    ) -> GetTagsForCalibrationOutput:
        """Executes the use case.

        Args:
            input_dto: The input data transfer object.

        Returns:
            The output data transfer object containing the list of tag names.

        Raises:
            CalibrationNotFoundError: If the specified calibration does not exist.
        """
        logger.info(
            f"Executing GetTagsForCalibrationUseCase for cal ID: {input_dto.calibration_id} "
            f"at timestamp: {input_dto.timestamp}"
        )

        # 1. Check if calibration exists (optional but good practice)
        calibration = await self._calibration_repo.get(id=input_dto.calibration_id)
        if not calibration:
            logger.warning(f"Calibration not found: {input_dto.calibration_id}")
            raise CalibrationNotFoundError(
                f"Calibration '{input_dto.calibration_id}' not found."
            )

        # 2. Get active tag associations for the calibration at the specified timestamp
        associations = (
            await self._calibration_repo.get_tag_associations_for_calibration(
                calibration_id=input_dto.calibration_id, active_at=input_dto.timestamp
            )
        )

        # 3. Get the actual Tag entities for the associated tag IDs
        tag_ids = [assoc.tag_id for assoc in associations]
        tags = []
        if tag_ids:
            tags = await self._tag_repo.get_by_ids(tag_ids)

        # 4. Extract tag names
        tag_names = sorted([tag.name for tag in tags])  # Sort for consistent output

        logger.info(
            f"Found {len(tag_names)} tags for calibration '{input_dto.calibration_id}'"
        )
        return GetTagsForCalibrationOutput(tag_names=tag_names)
