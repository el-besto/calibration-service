from typing import TYPE_CHECKING

from loguru import logger

from src.application.use_cases.exceptions import UseCaseError
from src.application.use_cases.tags.list_tags import ListTagsUseCase
from src.drivers.rest.schemas.tag_schemas import TagListResponse
from src.entities.exceptions import DatabaseOperationError
from src.interface_adapters.presenters.tag_presenter import TagPresenter

if TYPE_CHECKING:
    from src.application.use_cases.tags.list_tags import ListTagsOutput


class ListTagsController:
    def __init__(self, list_tags_use_case: ListTagsUseCase):
        self._list_tags_use_case = list_tags_use_case

    async def list_all_tags(self) -> TagListResponse:
        """Handles the request to list all tags."""
        try:
            output_dto: ListTagsOutput = await self._list_tags_use_case.execute()
            return TagPresenter.present_tag_list(output_dto.tags)
        except DatabaseOperationError as e:
            logger.error(f"Database error listing tags: {e}")
            raise  # Re-raise DatabaseOperationError
        except UseCaseError as e:
            logger.error(f"Unexpected use case error listing tags: {e}")
            raise UseCaseError(f"Internal error listing tags: {e}") from e
        except Exception as e:
            logger.exception(f"Unexpected internal error listing tags: {e}")
            raise UseCaseError("An unexpected internal error occurred.") from e
