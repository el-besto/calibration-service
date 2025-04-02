from uuid import UUID

from loguru import logger

from src.application.repositories.tag_repository import TagRepository
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.tag import Tag


class MockTagRepository(TagRepository):
    _tags_by_id: dict[UUID, Tag] = {}  # noqa: RUF012
    _tags_by_name: dict[str, Tag] = {}  # noqa: RUF012

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        logger.debug(f"Mock getting tag by id: {tag_id}")
        tag = self._tags_by_id.get(tag_id)
        # Return a copy to prevent modifying the stored object
        return Tag(**tag.__dict__) if tag else None

    async def get_by_name(self, name: str) -> Tag | None:
        logger.debug(f"Mock getting tag by name: {name}")
        tag = self._tags_by_name.get(name)
        # Return a copy
        return Tag(**tag.__dict__) if tag else None

    async def list_all(self) -> list[Tag]:
        logger.debug("Mock listing all tags")
        # Return copies of the stored tags
        return [Tag(**tag.__dict__) for tag in self._tags_by_id.values()]

    async def add(self, tag: Tag) -> Tag:
        logger.debug(f"Mock attempting to add tag: {tag.name}")
        # Check for duplicate name first
        if tag.name in self._tags_by_name:
            existing_tag = self._tags_by_name[tag.name]
            logger.warning(
                f"Mock: Tag with name '{tag.name}' already exists (ID: {existing_tag.id}). "
                "Raising error."
            )
            # Pass dummy exception as cause if needed, or None
            raise DatabaseOperationError(
                f"Tag name '{tag.name}' already exists.",
            ) from ValueError("Simulated duplicate name")

        # Make a copy to store
        new_tag = Tag(**tag.__dict__)

        # Add to both dictionaries
        self._tags_by_id[new_tag.id] = new_tag
        self._tags_by_name[new_tag.name] = new_tag
        logger.info(f"Mock added tag {new_tag.id} with name '{new_tag.name}'")

        # Return a copy of the added tag
        return Tag(**new_tag.__dict__)

    async def get_by_ids(self, tag_ids: list[UUID]) -> list[Tag]:
        """Retrieve multiple tags by their unique IDs from mock storage."""
        logger.debug(f"Mock getting tags by ids: {tag_ids}")
        found_tags = []
        for tag_id in tag_ids:
            if tag := self._tags_by_id.get(tag_id):
                found_tags.append(Tag(**tag.__dict__))  # Return copy
        return found_tags

    # Helper method for clearing the mock store in tests
    def clear(self):
        logger.info("Clearing MockTagRepository")
        self._tags_by_id.clear()
        self._tags_by_name.clear()
