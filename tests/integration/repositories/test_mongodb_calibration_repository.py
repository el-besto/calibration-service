# from datetime import UTC, datetime
# from typing import Any
# from unittest.mock import AsyncMock, MagicMock
# from uuid import uuid4
#
# import pytest
# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
#
# from src.entities.models.calibration import Measurement
# from src.entities.value_objects.calibration_type import CalibrationType
# from src.infrastructure.repositories.calibration_repository.mongodb_repository import (
#     MongoCalibrationRepository,
# )
# from tests.utils.test_entities import create_calibration, create_calibration_tag
#
#
# @pytest.fixture
# async def repo(client_mongo: AsyncIOMotorClient[Any]):
#     repo = MongoCalibrationRepository(client_mongo)
#     yield repo
#     await repo.collection.drop()
#
#
# @pytest.fixture
# def mock_collection() -> AsyncIOMotorCollection[dict[str, Any]]:
#     """Create a mock MongoDB collection for testing."""
#     collection = MagicMock(spec=AsyncIOMotorCollection)
#     collection.find_one = AsyncMock()
#     collection.update_one = AsyncMock()
#     collection.insert_one = AsyncMock()
#     collection.drop = AsyncMock()
#     return collection
#
#
# @pytest.mark.asyncio
# async def test_get_by_id_success(
#     repo: MongoCalibrationRepository,
#     mock_collection: AsyncIOMotorCollection[dict[str, Any]],
# ):
#     """Test successfully getting a calibration by ID."""
#     # ARRANGE
#     calibration = create_calibration(
#         measurement=Measurement(value=1.0, type=CalibrationType.gain),
#         tags=[],
#     )
#
#     # Mock the find_one response
#     mock_doc = {
#         "_id": calibration.id.bytes,  # Convert UUID to bytes for MongoDB
#         "measurement": {
#             "value": calibration.measurement.value,
#             "type": calibration.measurement.type,
#         },
#         "timestamp": str(calibration.timestamp),
#         "username": calibration.username,
#         "tags": [],
#     }
#     mock_collection.find_one = AsyncMock(return_value=mock_doc)
#     repo.collection = mock_collection
#
#     # ACT
#     result = await repo.get(id=calibration.id)
#
#     # ASSERT
#     assert result is not None
#     assert result.id == calibration.id
#     assert result.measurement.value == calibration.measurement.value
#     assert result.measurement.type == calibration.measurement.type
#     assert str(result.timestamp) == str(calibration.timestamp)
#     assert result.username == calibration.username
#     assert len(result.tags) == 0
#
#
# @pytest.mark.asyncio
# async def test_get_by_id_not_found(
#     repo: MongoCalibrationRepository,
#     mock_collection: AsyncIOMotorCollection[dict[str, Any]],
# ):
#     """Test getting a non-existent calibration by ID."""
#     # Mock the find_one response
#     mock_collection.find_one = AsyncMock(return_value=None)
#     repo.collection = mock_collection
#
#     # ACT
#     result = await repo.get(id=uuid4())
#
#     # ASSERT
#     assert result is None
#
#
# @pytest.mark.asyncio
# async def test_add_tags_success(
#     repo: MongoCalibrationRepository,
#     mock_collection: AsyncIOMotorCollection[dict[str, Any]],
# ):
#     """Test successfully adding tags to a calibration."""
#     # ARRANGE
#     calibration_id = uuid4()
#     calibration = create_calibration(
#         calibration_id=calibration_id,
#         measurement=Measurement(value=1.0, type=CalibrationType.gain),
#         tags=[],
#     )
#
#     # Mock the find_one response for the initial check
#     mock_doc = {
#         "_id": calibration.id.bytes,  # Convert UUID to bytes for MongoDB
#         "measurement": {
#             "value": calibration.measurement.value,
#             "type": calibration.measurement.type,
#         },
#         "timestamp": str(calibration.timestamp),
#         "username": calibration.username,
#         "tags": [],
#     }
#     mock_collection.find_one = AsyncMock(return_value=mock_doc)
#     repo.collection = mock_collection
#
#     # Create test tags
#     test_tags = [
#         create_calibration_tag(
#             tag_id=uuid4(),
#             calibration_id=calibration_id,
#             name=f"test_tag_{i}",
#         )
#         for i in range(3)
#     ]
#
#     # Mock the update_one response
#     mock_update_result = MagicMock()
#     mock_update_result.modified_count = 1
#     mock_collection.update_one = AsyncMock(return_value=mock_update_result)
#
#     # ACT
#     result = await repo.add_tags(calibration_id, test_tags)
#
#     # ASSERT
#     assert result is True
#
#     # Verify the tags were added by fetching the calibration
#     # Update the mock document to include the new tags
#     now = datetime.now(UTC).isoformat()
#     mock_doc["tags"] = [
#         {
#             "_id": tag.tag_id.bytes,  # Convert UUID to bytes for MongoDB
#             "tag_id": tag.tag_id.bytes,  # Add tag_id field
#             "calibration_id": tag.calibration_id.bytes,  # Convert UUID to bytes for MongoDB
#             "name": tag.name,
#             "archived_at": None,
#             "modified_at": now,
#             "created_at": now,
#         }
#         for tag in test_tags
#     ]
#     mock_collection.find_one = AsyncMock(return_value=mock_doc)
#
#     updated_calibration = await repo.get(id=calibration_id)
#     assert updated_calibration is not None
#     assert len(updated_calibration.tags) == len(test_tags)
#     for i, tag in enumerate(updated_calibration.tags):
#         assert tag.name == f"test_tag_{i}"
#
#
# @pytest.mark.asyncio
# async def test_add_tag_calibration_not_found(
#     repo: MongoCalibrationRepository,
#     mock_collection: AsyncIOMotorCollection[dict[str, Any]],
# ):
#     """Test adding tags to a non-existent calibration."""
#     # ARRANGE
#     calibration_id = uuid4()
#     test_tag = create_calibration_tag(
#         tag_id=uuid4(),
#         calibration_id=calibration_id,
#         name="test_tag",
#     )
#
#     # Mock the find_one response
#     mock_collection.find_one = AsyncMock(return_value=None)
#     repo.collection = mock_collection
#
#     # ACT
#     result = await repo.add_tags(calibration_id, [test_tag])
#
#     # ASSERT
#     assert result is False
