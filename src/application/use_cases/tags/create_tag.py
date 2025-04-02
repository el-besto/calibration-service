from dataclasses import dataclass

from src.application.repositories.tag_repository import TagRepository
from src.entities.models.tag import Tag


@dataclass(frozen=True)
class CreateTagInput:
    name: str


@dataclass(frozen=True)
class CreateTagOutput:
    tag: Tag


class CreateTagUseCase:
    def __init__(self, tag_repository: TagRepository):
        self._tag_repository = tag_repository

    async def execute(self, input_data: CreateTagInput) -> CreateTagOutput:
        """Executes the use case to create a new tag.

        Checks if a tag with the same name already exists.
        If it exists, returns the existing tag.
        If not, creates a new tag entity and adds it via the repository.

        Args:
            input_data: Contains the name for the new tag.

        Returns:
            Output containing the created or existing tag.
        """
        # Input validation (basic example - could be more complex)
        if not input_data.name or not input_data.name.strip():
            # Consider raising a specific validation error
            raise ValueError("Tag name cannot be empty.")

        # Check if tag already exists (repository handles potential duplicates on add,
        # but checking first can be clearer and avoid unnecessary DB interaction/errors)
        existing_tag = await self._tag_repository.get_by_name(input_data.name.strip())
        if existing_tag:
            # If tag exists, return it
            return CreateTagOutput(tag=existing_tag)

        # Create new tag entity
        new_tag = Tag(name=input_data.name.strip())

        # Add tag using the repository
        # The repository add method handles potential race conditions / duplicate names
        created_or_existing_tag = await self._tag_repository.add(new_tag)

        return CreateTagOutput(tag=created_or_existing_tag)
