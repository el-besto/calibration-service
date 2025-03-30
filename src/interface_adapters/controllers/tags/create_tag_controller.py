from loguru import logger

from src.application.use_cases.exceptions import UseCaseError, ValidationError
from src.application.use_cases.tags.create_tag import CreateTagInput, CreateTagUseCase
from src.drivers.rest.schemas.tag_schemas import TagCreateRequest, TagResponse
from src.entities.exceptions import DatabaseOperationError, InputParseError
from src.interface_adapters.presenters.tag_presenter import TagPresenter


class CreateTagController:
    def __init__(self, create_tag_use_case: CreateTagUseCase):
        self._create_tag_use_case = create_tag_use_case

    async def create_tag(self, request: TagCreateRequest) -> TagResponse:
        """Handles the request to create a new tag."""
        try:
            input_dto = CreateTagInput(name=request.name)
            output_dto = await self._create_tag_use_case.execute(input_dto)
            return TagPresenter.present_tag(output_dto.tag)
        except ValidationError as e:
            logger.warning(f"Validation error creating tag: {e}")
            raise InputParseError(str(e)) from e
        except DatabaseOperationError as e:
            logger.error(f"Database error creating tag '{request.name}': {e}")
            raise  # Re-raise DatabaseOperationError
        except UseCaseError as e:
            logger.error(f"Unexpected use case error creating tag: {e}")
            raise UseCaseError(f"Internal error creating tag: {e}") from e
        except Exception as e:
            logger.exception(
                f"Unexpected internal error creating tag '{request.name}': {e}"
            )
            raise UseCaseError("An unexpected internal error occurred.") from e
