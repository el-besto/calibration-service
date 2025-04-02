from datetime import datetime

from loguru import logger

from src.application.dtos.get_calibrations_by_tag_dtos import GetCalibrationsByTagInput
from src.application.use_cases.exceptions import (
    TagNotFoundError,
    UseCaseError,
)
from src.application.use_cases.tags.get_calibrations_by_tag import (
    GetCalibrationsByTagUseCase,
)
from src.drivers.rest.schemas.calibration_schemas import CalibrationReadResponse
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.interface_adapters.presenters.calibration_presenter import CalibrationPresenter


class GetCalibrationsByTagController:
    def __init__(self, get_calibrations_by_tag_use_case: GetCalibrationsByTagUseCase):
        self._get_calibrations_by_tag_use_case = get_calibrations_by_tag_use_case

    async def get_calibrations_by_tag(
        self,
        tag_name: str,
        timestamp: datetime,
        username: str | None,
    ) -> list[CalibrationReadResponse]:
        """Handles request to get calibrations associated with a tag at a specific time."""
        try:
            input_dto = GetCalibrationsByTagInput(
                tag_name=tag_name, timestamp=timestamp, username=username
            )
            output_dto = await self._get_calibrations_by_tag_use_case.execute(input_dto)

            # Use CalibrationPresenter as the output is a list of calibrations
            return CalibrationPresenter.present_calibration_list(
                output_dto.calibrations
            )

        except TagNotFoundError as e:
            logger.warning(
                f"Tag not found while getting calibrations for tag '{tag_name}': {e}"
            )
            raise NotFoundError(str(e)) from e
        except DatabaseOperationError as e:
            logger.error(
                f"Database error getting calibrations for tag '{tag_name}': {e}"
            )
            raise  # Re-raise DatabaseOperationError
        except UseCaseError as e:
            logger.error(f"Unexpected use case error getting calibrations by tag: {e}")
            raise UseCaseError("Internal error getting calibrations by tag.") from e
        except Exception as e:
            logger.exception(
                f"Unexpected internal error getting calibrations for tag '{tag_name}': {e}"
            )
            raise UseCaseError("An unexpected internal error occurred.") from e
