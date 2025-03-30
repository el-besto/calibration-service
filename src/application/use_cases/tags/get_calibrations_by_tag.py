from loguru import logger

from src.application.dtos.get_calibrations_by_tag_dtos import (
    GetCalibrationsByTagInput,
    GetCalibrationsByTagOutput,
)
from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.repositories.tag_repository import TagRepository
from src.application.use_cases.exceptions import (
    TagNotFoundError,
)


class GetCalibrationsByTagUseCase:
    """Use case to retrieve calibrations associated with a specific tag at a given time."""

    def __init__(
        self,
        tag_repository: TagRepository,
        calibration_repository: CalibrationRepository,
    ) -> None:
        self._tag_repo = tag_repository
        self._calibration_repo = calibration_repository

    async def execute(
        self, input_dto: GetCalibrationsByTagInput
    ) -> GetCalibrationsByTagOutput:
        """Executes the use case.

        Args:
            input_dto: The input data transfer object.

        Returns:
            The output data transfer object containing the list of calibrations.

        Raises:
            TagNotFoundError: If the specified tag does not exist.
        """
        logger.info(
            f"Executing GetCalibrationsByTagUseCase for tag: {input_dto.tag_name}"
        )

        # 1. Find the tag by name
        tag = await self._tag_repo.get_by_name(input_dto.tag_name)
        if not tag:
            logger.warning(f"Tag not found: {input_dto.tag_name}")
            raise TagNotFoundError(f"Tag '{input_dto.tag_name}' not found.")

        # 2. Get calibrations associated with this tag ID at the specified timestamp
        calibrations = await self._calibration_repo.get_by_tag_at_timestamp(
            tag_id=tag.id, timestamp=input_dto.timestamp, username=input_dto.username
        )

        logger.info(
            f"Found {len(calibrations)} calibrations for tag '{input_dto.tag_name}'"
        )
        return GetCalibrationsByTagOutput(calibrations=calibrations)
