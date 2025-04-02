from datetime import datetime
from typing import Any
from uuid import UUID

from loguru import logger

from src.application.repositories.calibration_repository import CalibrationRepository
from src.entities.models.calibration import Calibration
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.models.tag import Tag
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


class InMemoryCalibrationRepository(CalibrationRepository):
    _calibrations: dict[UUID, Calibration] = {}  # noqa: RUF012
    _associations: dict[UUID, dict[UUID, CalibrationTagAssociation]] = {}  # noqa: RUF012
    _tags: dict[UUID, Tag] = {}  # noqa: RUF012 --  Assume storage for Tag objects by ID

    def _get_calibration_sort_key(self, c: Calibration) -> datetime:
        """Helper function to get the sort key (timestamp) for a Calibration."""
        return c.timestamp.to_datetime()

    async def get(self, **filters: Any) -> Calibration | None:
        calibration_id = filters.get("id")
        if calibration_id:
            calibration = self._calibrations.get(calibration_id)
            if calibration:
                # Return a copy to prevent modification of stored object
                return Calibration(**calibration.__dict__)
        logger.debug(f"Calibration not found for filters: {filters}")
        return None

    async def add_calibration(self, calibration: Calibration) -> Calibration:
        if calibration.id in self._calibrations:
            logger.warning(
                f"Attempted to add existing calibration {calibration.id}. Returning existing."
            )
            return Calibration(**self._calibrations[calibration.id].__dict__)
        logger.debug(f"Adding new calibration {calibration.id}")
        new_calibration = Calibration(**calibration.__dict__)
        new_calibration.tags = []
        self._calibrations[new_calibration.id] = new_calibration
        return Calibration(**new_calibration.__dict__)

    async def add_tags(
        self,
        calibration_id: UUID,
        calibration_tag_associations: list[CalibrationTagAssociation] | None = None,
    ) -> bool:
        if calibration_id not in self._calibrations:
            logger.error(f"Cannot add tags: Calibration {calibration_id} not found.")
            return False
        if not calibration_tag_associations:
            logger.debug(
                f"No tags provided to add for calibration {calibration_id}. Skipping."
            )
            return True
        if calibration_id not in self._associations:
            self._associations[calibration_id] = {}
        added_count = 0
        for assoc in calibration_tag_associations:
            if assoc.calibration_id != calibration_id:
                logger.warning(
                    f"Skipping mock association {assoc.id} for cal {calibration_id} due to mismatch cal_id {assoc.calibration_id}."
                )
                continue
            logger.debug(
                f"Adding/updating association {assoc.id} for calibration {calibration_id}"
            )
            self._associations[calibration_id][assoc.id] = CalibrationTagAssociation(
                **assoc.__dict__
            )
            added_count += 1
        return added_count > 0

    async def get_tag_associations_for_calibration(
        self, calibration_id: UUID, active_at: datetime | None = None
    ) -> list[CalibrationTagAssociation]:
        logger.debug(
            f"Getting associations for calibration {calibration_id}, active_at: {active_at}"
        )
        calibration_associations = self._associations.get(calibration_id, {})
        results = []
        for assoc in calibration_associations.values():
            if (
                active_at is not None
                and assoc.archived_at is not None
                and assoc.archived_at <= active_at
            ):
                continue
            results.append(CalibrationTagAssociation(**assoc.__dict__))
        logger.debug(
            f"Found {len(results)} associations for calibration {calibration_id}"
        )
        return results

    async def update_tag_association(
        self, association: CalibrationTagAssociation
    ) -> CalibrationTagAssociation | None:
        calibration_id = association.calibration_id
        association_id = association.id
        if (
            calibration_id in self._associations
            and association_id in self._associations[calibration_id]
        ):
            logger.debug(
                f"Updating association {association_id} for calibration {calibration_id}"
            )
            updated_association = CalibrationTagAssociation(**association.__dict__)
            self._associations[calibration_id][association_id] = updated_association
            return CalibrationTagAssociation(**updated_association.__dict__)
        logger.warning(
            f"Attempted to update non-existent association {association_id} for cal {calibration_id}."
        )
        return None

    def clear(self):
        self._calibrations.clear()
        self._associations.clear()
        logger.info("MockCalibrationRepository cleared.")

    async def list_by_filters(
        self,
        username: str | None = None,
        timestamp: Iso8601Timestamp | None = None,
        calibration_type: CalibrationType | None = None,
        tags: list[str] | None = None,
    ) -> list[Calibration]:
        """Lists calibrations from mock storage based on optional filters."""
        logger.debug(
            f"Mock listing calibrations by filters: user={username}, ts={timestamp}, type={calibration_type}, tags={tags}"
        )
        results = []
        for cal in self._calibrations.values():
            match = True
            if username is not None and cal.username != username:
                match = False
            if timestamp is not None and cal.timestamp != timestamp:
                match = False
            if (
                calibration_type is not None
                and cal.measurement.type != calibration_type
            ):
                match = False

            # Filter by tags if provided
            if tags is not None:
                # Get active tag names for the current calibration
                # Note: This mock requires a synchronous way to get active tags or needs adjustment
                # For simplicity, assume tags are directly stored or fetched easily (needs refinement)
                # We need the association data here to check active tags.
                current_cal_assocs = self._associations.get(cal.id, {})
                active_tag_names = set()
                for assoc in current_cal_assocs.values():
                    if assoc.archived_at is None:  # Check if association is active
                        tag = self._tags.get(assoc.tag_id)  # Look up tag by ID
                        if tag:
                            active_tag_names.add(tag.name)

                # Check if *all* required tags are present in the active tags
                if not set(tags).issubset(active_tag_names):
                    match = False

            if match:
                entity = Calibration(**cal.__dict__)
                # Populate tags correctly based on associations
                current_cal_assocs = self._associations.get(cal.id, {})
                entity.tags = []
                for assoc in current_cal_assocs.values():
                    if assoc.archived_at is None:
                        tag = self._tags.get(assoc.tag_id)  # Look up tag by ID
                        if tag:
                            entity.tags.append(tag)
                results.append(entity)

        # Sort results
        results.sort(key=self._get_calibration_sort_key, reverse=True)
        logger.debug(f"Mock found {len(results)} calibrations matching filters.")
        return results

    # Add missing abstract method implementation
    async def get_by_tag_at_timestamp(
        self,
        tag_id: UUID,
        timestamp: datetime,
        username: str | None = None,
    ) -> list[Calibration]:
        """Mock implementation for retrieving calibrations by tag at a timestamp."""
        logger.debug(
            f"Mock get_by_tag_at_timestamp called with tag_id={tag_id}, ts={timestamp}, user={username}"
        )
        # This mock needs to check associations to find matching calibration IDs
        # then filter those calibrations by the timestamp logic and optional username.
        matching_cal_ids = set()
        for cal_id, associations_dict in self._associations.items():
            for assoc in associations_dict.values():
                if assoc.tag_id == tag_id:
                    # Check if association was active at the given timestamp
                    created_dt = assoc.created_at
                    archived_dt = assoc.archived_at

                    is_active = created_dt <= timestamp and (
                        archived_dt is None or archived_dt > timestamp
                    )
                    if is_active:
                        matching_cal_ids.add(cal_id)
                        break  # Found an active association for this cal, move to next cal

        # Filter calibrations by ID, timestamp, and username
        results = []
        for cal_id in matching_cal_ids:
            cal = self._calibrations.get(cal_id)
            if cal:
                # Additionally filter by username if provided
                if username is not None and cal.username != username:
                    continue

                # Important: The calibration itself must also exist at or before the timestamp
                # Although the association check handles tag timing, a calibration created *after*
                # the query timestamp shouldn't be included.
                if cal.timestamp.to_datetime() <= timestamp:
                    # Return a copy
                    entity = Calibration(**cal.__dict__)
                    entity.tags = []  # Tags are not populated in this mock method
                    results.append(entity)

        # Sort results
        results.sort(key=self._get_calibration_sort_key, reverse=True)
        logger.debug(f"Mock found {len(results)} calibrations for tag {tag_id}.")
        return results
