from uuid import UUID

from loguru import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.application.repositories.tag_repository import TagRepository
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.tag import Tag
from src.infrastructure.orm_models import TagORM


class SqlAlchemyTagRepository(TagRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        try:
            stmt = select(TagORM).where(TagORM.id == tag_id)
            result = await self.session.execute(stmt)
            orm_tag = result.scalars().first()
            return orm_tag.to_entity() if orm_tag else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tag by id {tag_id}: {e}")
            raise DatabaseOperationError("Failed to retrieve tag by ID") from e

    async def get_by_name(self, name: str) -> Tag | None:
        try:
            stmt = select(TagORM).where(TagORM.name == name)
            result = await self.session.execute(stmt)
            orm_tag = result.scalars().first()
            return orm_tag.to_entity() if orm_tag else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tag by name '{name}': {e}")
            raise DatabaseOperationError("Failed to retrieve tag by name") from e

    async def list_all(self) -> list[Tag]:
        try:
            stmt = select(TagORM).order_by(TagORM.name)
            result = await self.session.execute(stmt)
            orm_tags = result.scalars().all()
            return [tag.to_entity() for tag in orm_tags]
        except SQLAlchemyError as e:
            logger.error(f"Database error listing all tags: {e}")
            raise DatabaseOperationError("Failed to list tags") from e

    async def add(self, tag: Tag) -> Tag:
        orm_tag = TagORM.from_entity(tag)
        self.session.add(orm_tag)
        try:
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(orm_tag)
            logger.info(
                f"Successfully added tag {orm_tag.id} with name '{orm_tag.name}'"
            )
            return orm_tag.to_entity()
        except IntegrityError as e:
            await self.session.rollback()
            error_str = str(e).lower()
            is_unique_name_violation = "unique constraint" in error_str and (
                "tags.name" in error_str or "tags_name_key" in error_str
            )
            if is_unique_name_violation:
                logger.warning(
                    f"IntegrityError adding tag: name '{tag.name}' likely already exists. {e}"
                )
                raise DatabaseOperationError(
                    f"Tag name '{tag.name}' already exists."
                ) from e
            logger.error(f"Unhandled IntegrityError adding tag '{tag.name}': {e}")
            raise DatabaseOperationError(
                "Failed to add tag due to data integrity issue."
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error adding tag '{tag.name}': {e}")
            raise DatabaseOperationError("Failed to add tag.") from e

    async def get_by_ids(self, tag_ids: list[UUID]) -> list[Tag]:
        """Retrieve multiple tags by their unique IDs using PostgreSQL."""
        if not tag_ids:
            return []
        try:
            # Use the 'in_' operator for efficient querying
            stmt = select(TagORM).where(TagORM.id.in_(tag_ids))
            result = await self.session.execute(stmt)
            orm_tags = result.scalars().all()
            return [tag.to_entity() for tag in orm_tags]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tags by IDs: {tag_ids} - {e}")
            raise DatabaseOperationError("Failed to retrieve tags by IDs") from e
