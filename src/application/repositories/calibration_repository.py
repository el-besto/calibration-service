from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from src.entities.models.calibration import Calibration
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


class CalibrationRepository(ABC):
    """Abstract base class for calibration repositories.

    This interface defines the contract for implementing calibration storage.
    """

    @abstractmethod
    async def get(self, **filters: Any) -> Calibration | None:
        """Retrieve a calibration by its filters.

        Args:
            **filters: Arbitrary keyword arguments for filtering calibrations.

        Returns:
            Calibration | None: The found calibration or None if not found.
        """

    @abstractmethod
    async def add_tags(
        self,
        calibration_id: UUID,
        calibration_tag_associations: list[CalibrationTagAssociation] | None = None,
    ) -> bool:
        """Add tag associations to a calibration.

        Args:
            calibration_id: The ID of the calibration to add associations to.
            calibration_tag_associations: The list of associations to add. If None, no associations will be added.

        Returns:
            bool: True if the associations were added successfully, False otherwise.
        """

    @abstractmethod
    async def add_calibration(
        self,
        calibration: Calibration,
    ) -> Calibration:
        """Add a new calibration.

        Args:
            calibration: The calibration entity to add.

        Returns:
            The added calibration entity.
        """

    @abstractmethod
    async def get_tag_associations_for_calibration(
        self, calibration_id: UUID, active_at: datetime | None = None
    ) -> list[CalibrationTagAssociation]:
        """
        Retrieves tag associations for a given calibration ID.

        :param calibration_id: The ID of the calibration.
        :param active_at: If provided, only return associations that were active
                          (not archived or archived after this datetime) at this time.
        :return: A list of CalibrationTagAssociation objects.
        """

    @abstractmethod
    async def update_tag_association(
        self, association: CalibrationTagAssociation
    ) -> CalibrationTagAssociation | None:
        """Updates an existing tag association.

        Typically used to update the archived_at status.

        Args:
            association: The association entity with updated values.

        Returns:
            The updated association entity, or None if the association was not found.
        """

    @abstractmethod
    async def list_by_filters(
        self,
        username: str | None = None,
        timestamp: Iso8601Timestamp | None = None,
        calibration_type: CalibrationType | None = None,
        tags: list[str] | None = None,
    ) -> list[Calibration]:
        """Lists calibrations based on optional filters."""

    @abstractmethod
    async def get_by_tag_at_timestamp(
        self, tag_id: UUID, timestamp: datetime, username: str | None = None
    ) -> list[Calibration]:
        """Retrieves calibrations associated with a specific tag that were active at a given timestamp,
           optionally filtered by username.

        Args:
            tag_id: The ID of the tag to filter by.
            timestamp: The point in time to check for active associations.
                       An association is active if added_at <= timestamp and (archived_at is None or archived_at > timestamp).
            username: Optional username to further filter the calibrations.

        Returns:
            A list of Calibration entities matching the criteria.
        """
