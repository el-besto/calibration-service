from uuid import UUID

from loguru import logger

from src.application.repositories.tag_repository import TagRepository
from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
    UseCaseError,
)
from src.application.use_cases.tags.add_tag_to_calibration import (
    AddTagToCalibrationInput,
    AddTagToCalibrationUseCase,
)
from src.application.use_cases.tags.create_tag import CreateTagInput, CreateTagUseCase
from src.drivers.rest.schemas.tag_schemas import (
    TagOperationRequest,
    TagOperationResponse,
)
from src.entities.exceptions import DatabaseOperationError, NotFoundError
from src.entities.models.tag import Tag
from src.interface_adapters.presenters.tag_presenter import TagPresenter


class AddTagToCalibrationController:
    def __init__(
        self,
        add_tag_use_case: AddTagToCalibrationUseCase,
        create_tag_use_case: CreateTagUseCase,  # Needed for get_or_create logic
        tag_repository: TagRepository,  # Needed for get_or_create logic
    ):
        self._add_tag_use_case = add_tag_use_case
        self._create_tag_use_case = create_tag_use_case
        self._tag_repository = tag_repository

    async def _get_or_create_tag(self, tag_name: str) -> Tag:
        """Helper to find a tag by name or create it if it doesn't exist."""
        tag = await self._tag_repository.get_by_name(tag_name)
        if tag:
            return tag
        logger.info(f"Tag '{tag_name}' not found, attempting to create it.")
        try:
            # Use the injected CreateTagUseCase
            input_dto = CreateTagInput(name=tag_name)
            output_dto = await self._create_tag_use_case.execute(input_dto)
            logger.info(f"Created new tag '{tag_name}' with ID {output_dto.tag.id}")
            return output_dto.tag  # noqa: TRY300
        except DatabaseOperationError as e:
            # Handle potential race condition if tag created between get and create attempt
            if "already exists" in str(e).lower():
                logger.warning(
                    f"Race condition: Tag '{tag_name}' created concurrently. Fetching again."
                )
                tag = await self._tag_repository.get_by_name(tag_name)
                if tag:
                    return tag
            logger.error(f"Failed to create tag '{tag_name}' during get_or_create: {e}")
            # Raise a specific error or re-raise to indicate failure
            raise DatabaseOperationError(
                f"Could not get or create tag '{tag_name}' due to database error."
            ) from e
        except Exception as e:  # Catch other potential errors from CreateTagUseCase
            logger.error(
                f"Unexpected error creating tag '{tag_name}' during get_or_create: {e}"
            )
            raise UseCaseError(
                f"Unexpected error getting or creating tag '{tag_name}'."
            ) from e

    async def add_tag_to_calibration(
        self, calibration_id: UUID, request: TagOperationRequest
    ) -> TagOperationResponse:
        """Handles request to associate a tag with a calibration by tag name."""
        try:
            tag_name = request.tag
            # Use the integrated get_or_create logic
            tag = await self._get_or_create_tag(tag_name)
            # Note: _get_or_create_tag now raises errors if it fails,
            # so we don't need the 'if not tag:' check here.

            input_dto = AddTagToCalibrationInput(
                calibration_id=calibration_id, tag_id=tag.id
            )
            await self._add_tag_use_case.execute(input_dto)
            return TagPresenter.present_tag_added()

        except (CalibrationNotFoundError, TagNotFoundError) as e:
            logger.warning(
                f"Not found error adding tag '{request.tag}' to cal {calibration_id}: {e}"
            )
            raise NotFoundError(str(e)) from e
        except DatabaseOperationError as e:
            # Catch DB errors from both _get_or_create_tag and _add_tag_use_case
            logger.error(
                f"Database error involving tag '{request.tag}' and cal {calibration_id}: {e}"
            )
            raise  # Re-raise DatabaseOperationError
        except UseCaseError as e:
            # Catch UseCase errors from both _get_or_create_tag and _add_tag_use_case
            logger.error(
                f"Use case error involving tag '{request.tag}' and cal {calibration_id}: {e}"
            )
            # Consider if a more specific message is needed based on origin
            raise UseCaseError("Internal error processing tag association.") from e
        except Exception as e:
            logger.exception(
                f"Unexpected internal error adding tag '{request.tag}' to cal {calibration_id}: {e}"
            )
            raise UseCaseError("An unexpected internal error occurred.") from e
