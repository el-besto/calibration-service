from datetime import datetime
from typing import Any
from uuid import UUID

from bson import Binary
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from src.application.repositories.calibration_repository import CalibrationRepository
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.calibration import Calibration, Iso8601Timestamp
from src.entities.models.calibration_tag import CalibrationTag
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.value_objects.calibration_type import CalibrationType, Measurement


class MongoCalibrationRepository(CalibrationRepository):
    """MongoDB implementation of the calibration repository."""

    def __init__(self, client: AsyncIOMotorClient[Any]):
        """Initialize the repository.

        Args:
            client: The MongoDB client.
        """
        self.collection = client.calibrations.calibration

    async def get(self, **filters: Any) -> Calibration | None:
        """Get a calibration by its filters.

        Args:
            **filters: The filters to apply.

        Returns:
            Calibration | None: The calibration if found, None otherwise.

        Raises:
            DatabaseOperationError: If there is an error accessing the database.
        """
        filters = self.__get_filters(filters)
        try:
            document = await self.collection.find_one(filters)
            return self.__to_calibration_entity(document) if document else None
        except Exception as e:
            raise DatabaseOperationError(
                "MongoCalibrationRepository error",
            ) from e

    async def add_tags(
        self,
        calibration_id: UUID,
        calibration_tag_associations: list[CalibrationTagAssociation] | None = None,
    ) -> bool:
        """Add tags to a calibration.

        Args:
            calibration_id: The ID of the calibration to add tags to.
            calibration_tag_associations: The tags to add.

        Returns:
            bool: True if the tags were added, False otherwise.

        Raises:
            DatabaseOperationError: If there is an error accessing the database.
        """
        try:
            # Check if calibration exists
            calibration = await self.get(id=calibration_id)
            if not calibration:
                return False

            # Add tags to calibration
            r = await self.collection.update_one(
                {"_id": Binary.from_uuid(calibration_id)},
                {
                    "$push": {
                        "tags": {
                            "$each": [
                                self.__calibration_tag_to_doc(tag)
                                for tag in calibration_tag_associations or []
                            ],
                        },
                    },
                },
            )
            return bool(r.modified_count)
        except Exception as e:
            raise DatabaseOperationError(
                "MongoCalibrationRepository error",
            ) from e

    async def add_calibration(
        self,
        calibration: Calibration,
    ) -> Calibration:
        """Add a new calibration.

        Args:
            calibration: The calibration to add.

        Returns:
            Calibration: The added calibration.

        Raises:
            DatabaseOperationError: If there is an error accessing the database.
        """
        try:
            calibration_doc = self.__calibration_to_doc(calibration, None)
            await self.collection.insert_one(calibration_doc)
            return calibration
        except Exception as e:
            raise DatabaseOperationError(
                "MongoCalibrationRepository error",
            ) from e

    @staticmethod
    def __get_filters(filters_args: dict[str, Any]) -> dict[str, Binary]:
        """Get the MongoDB filters from the arguments.

        Args:
            filters_args: The filter arguments.

        Returns:
            dict[str, Binary]: The MongoDB filters.
        """
        filters = {}
        if f := filters_args.get("calibration_id"):
            filters["_id"] = Binary.from_uuid(f)
        return filters  # pyright: ignore [reportUnknownVariableType]

    def __calibration_to_doc(
        self,
        calibration: Calibration,
        calibration_tags: list[Any] | None = None,
    ) -> dict[str, Any]:
        """Convert a calibration to a MongoDB document.

        Args:
            calibration: The calibration to convert.
            calibration_tags: The tags to add.

        Returns:
            dict[str, Any]: The MongoDB document.
        """
        tags = []
        if calibration_tags is not None:
            tags.extend(
                [self.__calibration_tag_to_doc(tag) for tag in calibration_tags],
            )
        return {
            "_id": Binary.from_uuid(calibration.id),
            "measurement": {
                "_id": Binary.from_uuid(calibration.id),
                "value": calibration.measurement.value,
                "type": calibration.measurement.type,
            },
            "timestamp": calibration.timestamp.to_datetime().isoformat(),
            "username": calibration.username,
            "tags": tags,
        }

    @staticmethod
    def __calibration_tag_to_doc(tag: Any) -> dict[str, Any]:
        """Convert a calibration tag to a MongoDB document.

        Args:
            tag: The tag to convert.

        Returns:
            dict[str, Any]: The MongoDB document.
        """
        return {
            "_id": Binary.from_uuid(tag.id),
        }

    def __to_calibration_entity(self, obj: dict[str, Any]) -> Calibration:
        """Convert a MongoDB document to a calibration entity.

        Args:
            obj: The MongoDB document.

        Returns:
            Calibration: The calibration entity.
        """
        return Calibration(
            measurement=Measurement(
                value=obj["measurement"]["value"],
                type=obj["measurement"]["type"],
            ),
            timestamp=Iso8601Timestamp(obj["timestamp"]),
            username=obj["username"],
            tags=[self.__to_calibration_tag_entity(tag) for tag in obj["tags"]],
            id=UUID(bytes=obj["_id"]),
        )

    @staticmethod
    def __to_calibration_tag_entity(obj: dict[str, Any]) -> Any:
        """Convert a MongoDB document to a calibration tag entity.

        Args:
            obj: The MongoDB document.

        Returns:
            CalibrationTag: The calibration tag entity.
        """
        return CalibrationTag(
            name=obj.get("name", ""),
            tag_id=UUID(bytes=obj.get("tag_id")) if obj.get("tag_id") else UUID(int=0),
            calibration_id=UUID(bytes=obj.get("calibration_id"))
            if obj.get("calibration_id")
            else UUID(int=0),
            archived_at=datetime.fromisoformat(obj["archived_at"])
            if obj.get("archived_at")
            else None,
            created_at=datetime.fromisoformat(
                obj.get("created_at", datetime.min.isoformat())  # noqa: DTZ901
            ),
            modified_at=datetime.fromisoformat(
                obj.get("modified_at", datetime.min.isoformat())  # noqa: DTZ901
            ),
            id=UUID(bytes=obj["_id"]),
        )

    async def get_tag_associations_for_calibration(
        self, calibration_id: UUID, active_at: datetime | None = None
    ) -> list[CalibrationTagAssociation]:
        """Retrieves tag associations for a given calibration ID (STUBBED)."""
        logger.warning(
            "MongoCalibrationRepository.get_tag_associations_for_calibration not implemented"
        )
        return []

    async def update_tag_association(
        self, association: CalibrationTagAssociation
    ) -> CalibrationTagAssociation | None:
        """Updates an existing tag association in the database (STUBBED)."""
        logger.warning(
            "MongoCalibrationRepository.update_tag_association not implemented"
        )
        return None

    async def list_by_filters(
        self,
        username: str | None = None,
        timestamp: Iso8601Timestamp | None = None,
        calibration_type: CalibrationType | None = None,
        tags: list[str] | None = None,
    ) -> list[Calibration]:
        """Lists calibrations from MongoDB based on optional filters.

        Args:
            username: The username to filter by.
            timestamp: The timestamp to filter by.
            calibration_type: The calibration type to filter by.
            tags: The list of tags to filter by.

        Returns:
            list[Calibration]: The list of calibrations that match the filters.

        Raises:
            DatabaseOperationError: If there is an error accessing the database.
        """
        try:
            query_filter = {}
            if username is not None:
                query_filter["username"] = username
            if timestamp is not None:
                # Assuming exact timestamp match
                query_filter["timestamp"] = timestamp.to_datetime().isoformat()
            if calibration_type is not None:
                query_filter["measurement.type"] = calibration_type.value

            # Add tag filtering if tags are provided
            if tags:
                # MongoDB requires matching the tag *name* within the embedded tags array
                # Note: This assumes tags are stored as embedded documents with a 'name' field
                # Adjust if the schema is different (e.g., just storing names or IDs)
                # Also assumes the embedded tag document has an 'archived_at' field for active check
                query_filter["tags"] = {
                    "$elemMatch": {
                        "name": {"$in": tags},
                        "archived_at": None,  # Check that the association is active
                    }
                }
                # If you need to match *all* tags, the query is more complex:
                # query_filter["$and"] = [
                #     {"tags": {"$elemMatch": {"name": tag, "archived_at": None}}} for tag in tags
                # ]

            cursor = self.collection.find(query_filter).sort("timestamp", -1)
            results = []
            async for doc in cursor:
                results.append(self.__to_calibration_entity(doc))
            return results

        except Exception as e:
            logger.error(f"MongoDB error listing calibrations by filters: {e}")
            raise DatabaseOperationError(
                "Failed to list calibrations from MongoDB"
            ) from e

    async def get_by_tag_at_timestamp(
        self,
        tag_id: UUID,
        timestamp: datetime,
        username: str | None = None,
    ) -> list[Calibration]:
        """Retrieves calibrations associated with a specific tag that were active at a given timestamp,
        optionally filtered by username, using MongoDB.
        """
        try:
            # Build the $elemMatch query for the tags array
            # Assumes tags array contains embedded docs with 'tag_id', 'created_at', 'archived_at'
            # Adjust fields if MongoDB schema differs
            tag_match_filter = {
                "$elemMatch": {
                    "tag_id": Binary.from_uuid(tag_id),
                    "created_at": {"$lte": timestamp.isoformat()},
                    "$or": [
                        {"archived_at": None},
                        {"archived_at": {"$gt": timestamp.isoformat()}},
                    ],
                }
            }

            query_filter: dict[str, Any] = {"tags": tag_match_filter}

            # Add username filter if provided
            if username is not None:
                query_filter["username"] = username

            # Find matching calibrations, sort by timestamp
            cursor = self.collection.find(query_filter).sort("timestamp", -1)
            results: list[Calibration] = []
            async for doc in cursor:
                results.append(self.__to_calibration_entity(doc))
            return results

        except Exception as e:
            logger.error(f"MongoDB error getting calibrations by tag {tag_id}: {e}")
            raise DatabaseOperationError(
                "Failed to retrieve calibrations by tag from MongoDB."
            ) from e
