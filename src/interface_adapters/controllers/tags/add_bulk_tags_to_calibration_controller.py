from uuid import UUID

from loguru import logger

from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
    UseCaseError,
    ValidationError,
)
from src.application.use_cases.tags.add_bulk_tags_to_calibration import (
    AddBulkTagsToCalibrationInput,
    AddBulkTagsToCalibrationUseCase,
)
from src.drivers.rest.schemas.tag_schemas import (
    BulkAddTagsRequest,
    BulkAddTagsResponse,
)
from src.entities.exceptions import (
    DatabaseOperationError,
    InputParseError,
    NotFoundError,
)
from src.interface_adapters.presenters.tag_presenter import TagPresenter


class AddBulkTagsToCalibrationController:
    def __init__(self, add_bulk_tags_use_case: AddBulkTagsToCalibrationUseCase):
        self._add_bulk_tags_use_case = add_bulk_tags_use_case

    async def add_bulk_tags_to_calibration(
        self, calibration_id: UUID, request: BulkAddTagsRequest
    ) -> BulkAddTagsResponse:
        """Handles request to bulk associate tags with a calibration."""
        try:
            # Directly use tag_ids from the request
            input_dto = AddBulkTagsToCalibrationInput(
                calibration_id=calibration_id, tag_ids=request.tag_ids
            )
            # Pass the DTO directly to the use case instance
            output_dto = await self._add_bulk_tags_use_case(input_dto)
            return TagPresenter.present_bulk_add_output(output_dto)
        except ValidationError as e:
            logger.warning(
                f"Validation error bulk adding tags to cal {calibration_id}: {e}"
            )
            raise InputParseError(str(e)) from e
        except (CalibrationNotFoundError, TagNotFoundError) as e:
            # Catch errors if calibration or any tag ID is not found by the use case
            logger.warning(
                f"Not found error bulk adding tags to cal {calibration_id}: {e}"
            )
            raise NotFoundError(str(e)) from e
        except DatabaseOperationError as e:
            logger.error(
                f"Database error bulk adding tags to cal {calibration_id}: {e}"
            )
            raise  # Re-raise DatabaseOperationError
        except UseCaseError as e:
            logger.error(f"Unexpected use case error bulk adding tags: {e}")
            # Add specific context if possible, otherwise keep generic
            raise UseCaseError(f"Internal error bulk adding tags: {e}") from e
        except Exception as e:
            logger.exception(
                f"Unexpected internal error bulk adding tags to cal {calibration_id}: {e}"
            )
            raise UseCaseError("An unexpected internal error occurred.") from e
