from datetime import datetime
from typing import Any
from uuid import UUID

from loguru import logger

# from ulid import ULID
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.application.repositories.calibration_repository import CalibrationRepository
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.calibration import Calibration
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.infrastructure.orm_models import (
    CalibrationORM,
    CalibrationTagAssociationORM,
    TagORM,
)


class SqlAlchemyCalibrationRepository(CalibrationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, **filters: Any) -> Calibration | None:
        try:
            stmt = select(CalibrationORM).options(
                selectinload(CalibrationORM.tag_associations).selectinload(
                    CalibrationTagAssociationORM.tag
                )
            )

            if "id" in filters:
                stmt = stmt.where(CalibrationORM.id == filters["id"])
            # Add other potential filters if needed, e.g., by username/user_id
            # if "username" in filters: # Will change to user_id
            #     stmt = stmt.where(CalibrationORM.username == filters["username"])

            result = await self.session.execute(stmt)
            row = result.scalars().first()
            return row.to_entity() if row else None
        except SQLAlchemyError as e:
            logger.error(f"Database error during get calibration: {e}")
            # Pass message to DatabaseOperationError
            raise DatabaseOperationError("Failed to retrieve calibration") from e

    async def add_calibration(self, calibration: Calibration) -> Calibration:
        orm_calibration = CalibrationORM.from_entity(calibration)
        self.session.add(orm_calibration)
        try:
            await self.session.flush()  # Ensure ID is populated if needed before commit
            await self.session.commit()
            logger.info(f"Successfully added calibration {orm_calibration.id}")
            # Return the entity based on the committed ORM object
            return orm_calibration.to_entity()
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"IntegrityError adding calibration: {e}")
            raise DatabaseOperationError(
                "Failed to add calibration due to data integrity issue."
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error adding calibration: {e}")
            raise DatabaseOperationError("Failed to add calibration.") from e

    async def add_tags(
        self,
        calibration_id: UUID,
        calibration_tag_associations: list[CalibrationTagAssociation] | None = None,
    ) -> bool:
        if not calibration_tag_associations:
            return True

        orm_associations = []
        for assoc in calibration_tag_associations:
            if assoc.calibration_id != calibration_id:
                logger.warning(
                    f"Skipping association {assoc.id} for calibration {calibration_id} "
                    f"due to mismatched calibration_id {assoc.calibration_id}."
                )
                continue
            orm_associations.append(CalibrationTagAssociationORM.from_entity(assoc))

        if not orm_associations:
            logger.warning(
                f"No valid associations provided for calibration {calibration_id}"
            )
            return True

        try:
            self.session.add_all(orm_associations)
            await self.session.flush()
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Database integrity error adding tags for calibration {calibration_id}: {e}",
            )
            raise DatabaseOperationError(
                "Failed to add tag associations due to integrity constraint"
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error adding tags for calibration {calibration_id}: {e}",
            )
            raise DatabaseOperationError("Failed to add tag associations") from e
        else:
            return True

    async def get_tag_associations_for_calibration(
        self, calibration_id: UUID, active_at: datetime | None = None
    ) -> list[CalibrationTagAssociation]:
        try:
            stmt = select(CalibrationTagAssociationORM).where(
                CalibrationTagAssociationORM.calibration_id == calibration_id
            )

            if active_at is not None:
                stmt = stmt.where(
                    or_(
                        CalibrationTagAssociationORM.archived_at.is_(None),
                        CalibrationTagAssociationORM.archived_at > active_at,
                    )
                )

            stmt = stmt.options(selectinload(CalibrationTagAssociationORM.tag))

            result = await self.session.execute(stmt)
            associations = result.scalars().all()
            return [assoc.to_entity() for assoc in associations]
        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving tag associations for calibration {calibration_id}: {e}",
            )
            raise DatabaseOperationError("Failed to retrieve tag associations") from e

    async def update_tag_association(
        self, association: CalibrationTagAssociation
    ) -> CalibrationTagAssociation | None:
        try:
            existing_orm_assoc = await self.session.get(
                CalibrationTagAssociationORM, association.id
            )

            if not existing_orm_assoc:
                logger.warning(
                    f"Attempted to update non-existent tag association {association.id}"
                )
                return None

            existing_orm_assoc.archived_at = association.archived_at

            self.session.add(existing_orm_assoc)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(existing_orm_assoc)
            return existing_orm_assoc.to_entity()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error updating tag association {association.id}: {e}",
            )
            raise DatabaseOperationError("Failed to update tag association") from e

    async def list_by_filters(
        self,
        username: str | None = None,
        timestamp: Iso8601Timestamp | None = None,
        calibration_type: CalibrationType | None = None,
        tags: list[str] | None = None,
    ) -> list[Calibration]:
        """Lists calibrations from PostgreSQL based on optional filters."""
        try:
            stmt = select(CalibrationORM).options(
                selectinload(CalibrationORM.tag_associations).selectinload(
                    CalibrationTagAssociationORM.tag
                )
            )

            filters = []
            if username is not None:
                filters.append(CalibrationORM.username == username)
            if timestamp is not None:
                # Assuming exact timestamp match for now
                filters.append(CalibrationORM.timestamp == timestamp.to_datetime())
            if calibration_type is not None:
                filters.append(CalibrationORM.type == calibration_type)

            # Add tag filtering if tags are provided
            if tags:
                # Find tag IDs matching the provided tag names
                tag_ids_query = select(TagORM.id).where(TagORM.name.in_(tags))
                tag_ids_result = await self.session.execute(tag_ids_query)
                tag_ids = tag_ids_result.scalars().all()

                if not tag_ids:
                    # If no tags found matching the names, return empty list
                    return []

                # Filter calibrations that have an association with *any* of the found tag IDs
                # Ensure the association is currently active (not archived)
                filters.append(
                    CalibrationORM.tag_associations.any(
                        and_(
                            CalibrationTagAssociationORM.tag_id.in_(tag_ids),
                            CalibrationTagAssociationORM.archived_at.is_(None),
                        )
                    )
                )

            if filters:
                stmt = stmt.where(*filters)

            stmt = stmt.order_by(CalibrationORM.timestamp.desc())

            result = await self.session.execute(stmt)
            orm_calibrations = result.scalars().unique().all()
            return [cal.to_entity() for cal in orm_calibrations]

        except SQLAlchemyError as e:
            logger.error(f"Database error listing calibrations by filters: {e}")
            raise DatabaseOperationError(
                "Failed to list calibrations by filters"
            ) from e

    async def get_by_tag_at_timestamp(
        self, tag_id: UUID, timestamp: datetime, username: str | None = None
    ) -> list[Calibration]:
        """Retrieves calibrations associated with a specific tag that were active at a given timestamp,
        optionally filtered by username, using SQLAlchemy.
        """
        try:
            stmt = (
                select(CalibrationORM)
                .join(CalibrationORM.tag_associations)
                .options(
                    selectinload(CalibrationORM.tag_associations).selectinload(
                        CalibrationTagAssociationORM.tag
                    )
                )
                .where(
                    CalibrationTagAssociationORM.tag_id == tag_id,
                    CalibrationTagAssociationORM.created_at <= timestamp,
                    or_(
                        CalibrationTagAssociationORM.archived_at.is_(None),
                        CalibrationTagAssociationORM.archived_at > timestamp,
                    ),
                )
            )

            if username is not None:
                stmt = stmt.where(CalibrationORM.username == username)

            stmt = stmt.order_by(CalibrationORM.timestamp.desc())

            result = await self.session.execute(stmt)
            orm_calibrations = result.scalars().unique().all()
            return [cal.to_entity() for cal in orm_calibrations]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving calibrations by tag {tag_id} at {timestamp}: {e}"
            )
            raise DatabaseOperationError(
                "Failed to retrieve calibrations by tag."
            ) from e
