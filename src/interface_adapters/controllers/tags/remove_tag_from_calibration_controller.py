from uuid import UUID

from loguru import logger

from src.application.repositories.tag_repository import TagRepository
from src.application.use_cases.exceptions import (
    AssociationNotFoundError,
    CalibrationNotFoundError,
    TagNotFoundError,
    UseCaseError,
)
from src.application.use_cases.tags.remove_tag_from_calibration import (
    RemoveTagFromCalibrationInput,
    RemoveTagFromCalibrationUseCase,
)
from src.drivers.rest.schemas.tag_schemas import (
    TagOperationRequest,
    TagOperationResponse,
)
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.interface_adapters.presenters.tag_presenter import TagPresenter


class RemoveTagFromCalibrationController:
    def __init__(
        self,
        remove_tag_use_case: RemoveTagFromCalibrationUseCase,
        tag_repository: TagRepository,  # Needed to find tag ID by name
    ):
        self._remove_tag_use_case = remove_tag_use_case
        self._tag_repository = tag_repository

    async def remove_tag_from_calibration(
        self, calibration_id: UUID, request: TagOperationRequest
    ) -> TagOperationResponse:
        """Handles request to disassociate a tag from a calibration by tag name."""
        try:
            tag_name = request.tag
            # Find the tag by name first
            tag = await self._tag_repository.get_by_name(tag_name)
            if not tag:
                # Raise specific TagNotFoundError if tag doesn't exist
                raise TagNotFoundError(f"Tag '{tag_name}' not found.")  # noqa: TRY301

            input_dto = RemoveTagFromCalibrationInput(
                calibration_id=calibration_id, tag_id=tag.id
            )
            await self._remove_tag_use_case.execute(input_dto)
            return TagPresenter.present_tag_removed()

        except (
            CalibrationNotFoundError,
            TagNotFoundError,  # Catch from both explicit check and use case
            AssociationNotFoundError,
        ) as e:
            logger.warning(
                f"Not found error removing tag '{request.tag}' from cal {calibration_id}: {e}"
            )
            raise NotFoundError(str(e)) from e
        except DatabaseOperationError as e:
            # Could be from get_by_name or the use case execution
            logger.error(
                f"Database error removing tag '{request.tag}' from cal {calibration_id}: {e}"
            )
            raise  # Re-raise DatabaseOperationError
        except UseCaseError as e:
            logger.error(f"Unexpected use case error removing tag association: {e}")
            raise UseCaseError("Internal error removing tag association.") from e
        except Exception as e:
            logger.exception(
                f"Unexpected internal error removing tag '{request.tag}' from cal {calibration_id}: {e}"
            )
            raise UseCaseError("An unexpected internal error occurred.") from e
