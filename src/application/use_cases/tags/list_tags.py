from dataclasses import dataclass

from src.application.repositories.tag_repository import TagRepository
from src.entities.models.tag import Tag


@dataclass(frozen=True)
class ListTagsOutput:
    tags: list[Tag]


class ListTagsUseCase:
    def __init__(self, tag_repository: TagRepository):
        self._tag_repository = tag_repository

    async def execute(self) -> ListTagsOutput:
        """Executes the use case to list all tags."""
        all_tags = await self._tag_repository.list_all()
        return ListTagsOutput(tags=all_tags)
