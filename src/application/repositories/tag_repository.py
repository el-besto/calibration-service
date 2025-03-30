from abc import ABC, abstractmethod
from uuid import UUID

from src.entities.models.tag import Tag


class TagRepository(ABC):
    """Abstract base class for tag repositories."""

    @abstractmethod
    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        """Retrieve a tag by its unique ID."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Tag | None:
        """Retrieve a tag by its name (assuming names are unique)."""

    @abstractmethod
    async def list_all(self) -> list[Tag]:
        """Retrieve all tags."""

    @abstractmethod
    async def add(self, tag: Tag) -> Tag:
        """Add a new tag."""

    @abstractmethod
    async def get_by_ids(self, tag_ids: list[UUID]) -> list[Tag]:
        """Retrieve multiple tags by their unique IDs."""
