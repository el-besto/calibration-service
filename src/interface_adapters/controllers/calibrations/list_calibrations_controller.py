from typing import TYPE_CHECKING

from loguru import logger

from src.application.use_cases.calibrations.list_calibrations import (
    ListCalibrationsInput,
    ListCalibrationsUseCase,
)
from src.application.use_cases.exceptions import UseCaseError
from src.drivers.rest.schemas.calibration_schemas import CalibrationListResponse
from src.entities.exceptions import DatabaseOperationError, InputParseError
from src.interface_adapters.presenters.calibration_presenter import CalibrationPresenter

if TYPE_CHECKING:
    from src.application.use_cases.calibrations.list_calibrations import (
        ListCalibrationsOutput,
    )


class ListCalibrationsController:
    def __init__(self, list_calibrations_use_case: ListCalibrationsUseCase):
        self._list_calibrations_use_case = list_calibrations_use_case

    async def list_calibrations(
        self,
        # Define optional query parameters
        username: str | None = None,
        timestamp: str | None = None,
        calibration_type: str | None = None,
        tags: list[str] | None = None,
    ) -> CalibrationListResponse:
        """Handles the request to list calibrations based on filters."""
        try:
            # Create input DTO from query parameters
            input_dto = ListCalibrationsInput(
                username=username,
                timestamp_str=timestamp,
                calibration_type_str=calibration_type,
                tags=tags,
            )

            # Call the use case
            output_dto: ListCalibrationsOutput = await self._list_calibrations_use_case(
                input_dto
            )

            # Format the response using the presenter
            return CalibrationPresenter.present_list_output(output_dto)

        except InputParseError as e:
            logger.warning(f"Invalid filter value provided: {e}")
            raise  # Re-raise InputParseError for router to handle (e.g., 400 Bad Request)
        except DatabaseOperationError as e:
            logger.error(f"Database error listing calibrations: {e}")
            raise  # Re-raise for router (e.g., 500 Internal Server Error)
        except UseCaseError as e:
            logger.error(f"Unexpected use case error listing calibrations: {e}")
            raise  # Re-raise for router (e.g., 500 Internal Server Error)
        except Exception as e:
            logger.exception(f"Unexpected internal error listing calibrations: {e}")
            raise UseCaseError("An unexpected internal error occurred.") from e
