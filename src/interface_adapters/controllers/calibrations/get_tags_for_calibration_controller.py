from datetime import datetime
from uuid import UUID

from loguru import logger

# from src.application.use_cases.get_tags_for_calibration import (
#     GetTagsForCalibrationInput,
#     GetTagsForCalibrationUseCase,
# )
from src.application.use_cases.calibrations.get_tags_for_calibration import (
    GetTagsForCalibrationInput,
    GetTagsForCalibrationUseCase,
)
from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    UseCaseError,
)
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.interface_adapters.presenters.calibration_presenter import CalibrationPresenter


class GetTagsForCalibrationController:
    def __init__(self, get_tags_for_calibration_use_case: GetTagsForCalibrationUseCase):
        self._get_tags_for_calibration_use_case = get_tags_for_calibration_use_case

    async def get_tags_for_calibration(
        self,
        calibration_id: UUID,
        timestamp: datetime,
    ) -> list[str]:
        """Handles request to get tags associated with a calibration at a specific time."""
        try:
            input_dto = GetTagsForCalibrationInput(
                calibration_id=calibration_id, timestamp=timestamp
            )
            output_dto = await self._get_tags_for_calibration_use_case.execute(
                input_dto
            )
            # Use presenter for consistency and testability
            return CalibrationPresenter.present_calibration_tags(output_dto)
        except CalibrationNotFoundError as e:
            logger.warning(
                f"Not found error getting tags for cal {calibration_id}: {e}"
            )
            raise NotFoundError(str(e)) from e
        except DatabaseOperationError as e:
            logger.error(f"DB error getting tags for cal {calibration_id}: {e}")
            raise  # Re-raise
        except UseCaseError as e:
            logger.error(
                f"Unexpected use case error getting tags for cal {calibration_id}: {e}"
            )
            raise  # Re-raise
        except Exception as e:
            logger.exception(
                f"Unexpected error getting tags for cal {calibration_id}: {e}"
            )
            raise UseCaseError("An unexpected internal error occurred.") from e
