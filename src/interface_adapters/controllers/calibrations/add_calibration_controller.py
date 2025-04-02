from typing import TYPE_CHECKING

from loguru import logger

from src.application.use_cases.calibrations.add_calibration_use_case import (
    AddCalibrationInput,
    AddCalibrationUseCase,
)
from src.application.use_cases.exceptions import UseCaseError
from src.drivers.rest.schemas.calibration_schemas import (
    CalibrationCreateRequest,
    CalibrationCreateResponse,
)
from src.entities.exceptions import DatabaseOperationError, InputParseError
from src.interface_adapters.presenters.calibration_presenter import CalibrationPresenter

if TYPE_CHECKING:
    from src.application.use_cases.calibrations.add_calibration_use_case import (
        AddCalibrationOutput,
    )


class AddCalibrationController:
    def __init__(self, add_calibration_use_case: AddCalibrationUseCase):
        self._add_calibration_use_case = add_calibration_use_case

    async def create_calibration(
        self, request: CalibrationCreateRequest
    ) -> CalibrationCreateResponse:
        """Handles the request to create a new calibration."""
        try:
            input_dto = AddCalibrationInput(
                calibration_type=request.calibration_type,
                value=request.value,
                timestamp_str=request.timestamp,
                username=request.username,
            )
            output_dto: AddCalibrationOutput = await self._add_calibration_use_case(
                input_dto
            )
            return CalibrationPresenter.present_calibration_creation(output_dto)

        except InputParseError as e:
            logger.warning(f"Input parsing error creating calibration: {e}")
            raise  # Re-raise InputParseError to be handled by router/middleware
        except DatabaseOperationError as e:
            logger.error(f"Database error creating calibration: {e}")
            raise  # Re-raise DatabaseOperationError
        except UseCaseError as e:
            logger.error(f"Unexpected use case error creating calibration: {e}")
            raise  # Re-raise UseCaseError
        except Exception as e:
            # Catch-all for truly unexpected errors
            logger.exception(f"Unexpected internal error creating calibration: {e}")
            # Re-raise as a generic UseCaseError or let a global handler manage it
            raise UseCaseError("An unexpected internal error occurred.") from e
