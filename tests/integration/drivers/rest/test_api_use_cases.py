from datetime import UTC, datetime
import uuid
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture

# Import Schemas and Use Case DTOs/Models needed for mocking/assertions
from src.application.dtos.get_calibrations_by_tag_dtos import (
    GetCalibrationsByTagOutput,
)
from src.application.dtos.get_tags_for_calibration_dtos import (
    GetTagsForCalibrationOutput,
)
from src.application.use_cases.calibrations.add_calibration_use_case import (
    AddCalibrationInput,
    AddCalibrationOutput,
)
from src.application.use_cases.calibrations.get_tags_for_calibration import (
    GetTagsForCalibrationInput,
)
from src.application.use_cases.calibrations.list_calibrations import (
    ListCalibrationsInput,
    ListCalibrationsOutput,
)
from src.application.use_cases.tags.add_tag_to_calibration import (
    AddTagToCalibrationInput,
)
from src.application.use_cases.tags.get_calibrations_by_tag import GetCalibrationsByTagInput
from src.application.use_cases.tags.remove_tag_from_calibration import (
    RemoveTagFromCalibrationInput,
)
from src.drivers.rest.dependencies import (
    get_add_calibration_use_case,
    get_add_tag_to_calibration_use_case,
    get_get_calibrations_by_tag_use_case,
    get_get_tags_for_calibration_use_case,
    get_list_calibrations_use_case,
    get_remove_tag_from_calibration_use_case,
    get_tag_repository,
)
from src.drivers.rest.main import app
from src.entities.models.calibration import Calibration
from src.entities.models.tag import Tag
from src.entities.value_objects.calibration_type import CalibrationType, Measurement
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp

# Mark all tests as async
pytestmark = pytest.mark.asyncio

# --- Mock Repository for Tag Tests --- Needed by controllers
class MockTagRepo:
    async def get_by_name(self, name: str) -> Tag | None:
        # Simple mock: Return a tag object with a predictable ID based on name
        # This avoids needing global state or complex mocking logic here.
        print(f"MockTagRepo: get_by_name called for '{name}'")
        tag_id = uuid.uuid5(uuid.NAMESPACE_DNS, name) # Deterministic ID
        return Tag(id=tag_id, name=name, created_at=datetime.now(UTC))

    # Add other methods if needed by controllers, returning default values
    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        return None # Not strictly needed for these tests
    async def list_all(self) -> list[Tag]:
        return [] # Not strictly needed for these tests
    async def add(self, tag: Tag) -> Tag:
        return tag # Not strictly needed for these tests

# --- Fixtures for Mocked Use Cases ---


@pytest.fixture
def mock_add_calibration_use_case(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(name="AddCalibrationUseCase")


@pytest.fixture
def mock_list_calibrations_use_case(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(name="ListCalibrationsUseCase")


@pytest.fixture
def mock_add_tag_use_case(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(name="AddTagToCalibrationUseCase")


@pytest.fixture
def mock_remove_tag_use_case(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(name="RemoveTagFromCalibrationUseCase")


@pytest.fixture
def mock_get_calibrations_by_tag_use_case(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(name="GetCalibrationsByTagUseCase")


@pytest.fixture
def mock_get_tags_use_case(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(name="GetTagsForCalibrationUseCase")


# --- Helper Function for Mock Calibration Data ---
def create_mock_calibration(
    cal_id: UUID | None = None,
    cal_type: str = "gain",
    value: float = 123.45,
    timestamp: str | None = None,
    username: str = "testuser",
    tags: list[Tag] | None = None,
) -> Calibration:
    """Creates a mock Calibration object for testing."""
    if timestamp is None:
        timestamp_obj = Iso8601Timestamp(datetime.now(UTC).isoformat())
    else:
        timestamp_obj = Iso8601Timestamp(timestamp)

    measurement_obj = Measurement(type=CalibrationType(cal_type), value=value)

    return Calibration(
        id=cal_id or uuid4(),
        measurement=measurement_obj,
        timestamp=timestamp_obj,
        username=username,
        tags=tags or [],
    )


# --- Core Use Case Tests ---


# Use Case 1: Create a New Calibration
@pytest.mark.asyncio
async def test_uc1_create_calibration_success(
    async_client: AsyncClient,
    mock_add_calibration_use_case: AsyncMock,
):
    """Tests POST /calibrations success."""
    # Arrange
    test_uuid = uuid4()
    mock_calibration = create_mock_calibration(cal_id=test_uuid)
    mock_output_dto = AddCalibrationOutput(created_calibration=mock_calibration)
    mock_add_calibration_use_case.return_value = mock_output_dto

    app.dependency_overrides[get_add_calibration_use_case] = (
        lambda: mock_add_calibration_use_case
    )
    payload = {
        "calibration_type": "gain",
        "value": 100.5,
        "timestamp": "2023-01-01T12:00:00Z",
        "username": "test_user",
    }

    # Act
    response = await async_client.post("/calibrations", json=payload)

    # Assert
    assert response.status_code == 201
    assert response.json() == {"calibration_id": str(test_uuid)}
    mock_add_calibration_use_case.assert_awaited_once()
    # Check the input DTO passed to the use case
    call_args, _ = mock_add_calibration_use_case.call_args
    input_dto = call_args[0]
    assert isinstance(input_dto, AddCalibrationInput)
    assert input_dto.calibration_type == payload["calibration_type"]
    assert input_dto.value == payload["value"]
    assert input_dto.timestamp_str == payload["timestamp"]
    assert input_dto.username == payload["username"]

    # Clean up override
    del app.dependency_overrides[get_add_calibration_use_case]


# Use Case 2: Query Calibrations by Filter (No Filter)
@pytest.mark.asyncio
async def test_uc2_list_calibrations_success_no_filters(
    async_client: AsyncClient,
    mock_list_calibrations_use_case: AsyncMock,
):
    """Tests GET /calibrations success with no filters."""
    # Arrange
    mock_cal_1 = create_mock_calibration()
    mock_cal_2 = create_mock_calibration()
    mock_output = ListCalibrationsOutput(calibrations=[mock_cal_1, mock_cal_2])
    mock_list_calibrations_use_case.return_value = mock_output
    app.dependency_overrides[get_list_calibrations_use_case] = (
        lambda: mock_list_calibrations_use_case
    )

    # Act
    response = await async_client.get("/calibrations")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "calibrations" in response_data
    calibrations_list = response_data["calibrations"]
    assert isinstance(calibrations_list, list)
    assert len(calibrations_list) == 2
    # Basic check on structure (more detailed checks can be added)
    assert calibrations_list[0]["calibration_id"] == str(mock_cal_1.id)
    assert calibrations_list[1]["calibration_id"] == str(mock_cal_2.id)

    # Verify use case called with default input DTO
    mock_list_calibrations_use_case.assert_awaited_once()
    call_args, _ = mock_list_calibrations_use_case.call_args
    input_dto = call_args[0]
    assert isinstance(input_dto, ListCalibrationsInput)
    # Check default values based on ListCalibrationsInput definition
    assert input_dto.calibration_type_str is None
    assert input_dto.username is None
    assert input_dto.timestamp_str is None
    assert input_dto.tags is None

    # Clean up override
    del app.dependency_overrides[get_list_calibrations_use_case]


# Use Case 3a: Add a tag to a Calibration
@pytest.mark.asyncio
async def test_uc3a_add_tag_success(
    async_client: AsyncClient,
    mock_add_tag_use_case: AsyncMock,
):
    """Tests POST /calibrations/{id}/tags success."""
    # Arrange
    test_cal_id = uuid4()
    tag_payload = {"tag": "new_tag"}
    expected_tag_id = uuid.uuid5(uuid.NAMESPACE_DNS, tag_payload["tag"])

    mock_repo = MockTagRepo()
    app.dependency_overrides[get_tag_repository] = lambda: mock_repo

    mock_add_tag_use_case.execute.return_value = None
    app.dependency_overrides[get_add_tag_to_calibration_use_case] = (
        lambda: mock_add_tag_use_case
    )

    # Act
    response = await async_client.post(
        f"/calibrations/{test_cal_id}/tags", json=tag_payload
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Tag added successfully"}

    # Verify use case called correctly
    mock_add_tag_use_case.execute.assert_awaited_once()
    call_args, _ = mock_add_tag_use_case.execute.call_args
    input_dto = call_args[0]
    assert isinstance(input_dto, AddTagToCalibrationInput)
    assert input_dto.calibration_id == test_cal_id
    assert input_dto.tag_id == expected_tag_id

    # Clean up overrides
    del app.dependency_overrides[get_add_tag_to_calibration_use_case]
    del app.dependency_overrides[get_tag_repository]


# Use Case 3b: Removing a tag (using path parameter version)
@pytest.mark.asyncio
async def test_uc3b_remove_tag_success(
    async_client: AsyncClient,
    mock_remove_tag_use_case: AsyncMock,
):
    """Tests DELETE /calibrations/{id}/tags/{name} success."""
    # Arrange
    test_cal_id = uuid4()
    tag_name = "tag_to_remove"
    expected_tag_id = uuid.uuid5(uuid.NAMESPACE_DNS, tag_name)

    mock_repo = MockTagRepo()
    app.dependency_overrides[get_tag_repository] = lambda: mock_repo

    mock_remove_tag_use_case.execute.return_value = (
        None
    )
    app.dependency_overrides[get_remove_tag_from_calibration_use_case] = (
        lambda: mock_remove_tag_use_case
    )

    # Act
    response = await async_client.delete(
        f"/calibrations/{test_cal_id}/tags/{tag_name}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Tag removed successfully"}

    # Verify use case called correctly
    mock_remove_tag_use_case.execute.assert_awaited_once()
    call_args, _ = mock_remove_tag_use_case.execute.call_args
    input_dto = call_args[0]
    assert isinstance(input_dto, RemoveTagFromCalibrationInput)
    assert input_dto.calibration_id == test_cal_id
    assert input_dto.tag_id == expected_tag_id

    # Clean up overrides
    del app.dependency_overrides[get_remove_tag_from_calibration_use_case]
    del app.dependency_overrides[get_tag_repository]


# Use Case 4: Retrieve Calibrations by Tag
@pytest.mark.asyncio
async def test_uc4_get_calibrations_by_tag_success(
    async_client: AsyncClient,
    mock_get_calibrations_by_tag_use_case: AsyncMock,
):
    """Tests GET /tags/{name}/calibrations success."""
    # Arrange
    tag_name = "target_tag"
    mock_cal_1 = create_mock_calibration()
    mock_cal_2 = create_mock_calibration()
    mock_output = GetCalibrationsByTagOutput(calibrations=[mock_cal_1, mock_cal_2])
    mock_get_calibrations_by_tag_use_case.execute.return_value = mock_output

    app.dependency_overrides[get_get_calibrations_by_tag_use_case] = (
        lambda: mock_get_calibrations_by_tag_use_case
    )

    # Act
    response = await async_client.get(
        f"/tags/{tag_name}/calibrations"
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "calibrations" in response_data
    calibrations_list = response_data["calibrations"]
    assert isinstance(calibrations_list, list)
    assert len(calibrations_list) == 2
    assert calibrations_list[0]["calibration_id"] == str(mock_cal_1.id)
    assert calibrations_list[1]["calibration_id"] == str(mock_cal_2.id)

    # Verify use case execute method was awaited and called
    mock_get_calibrations_by_tag_use_case.execute.assert_awaited_once()
    call_args, _ = mock_get_calibrations_by_tag_use_case.execute.call_args
    input_dto = call_args[0] # Assuming controller passes DTO
    # Uncommented and verified assertions for input DTO
    assert isinstance(input_dto, GetCalibrationsByTagInput)
    assert input_dto.tag_name == tag_name
    # Add checks for default timestamp/username if applicable, based on controller logic
    # assert input_dto.timestamp is not None
    # assert input_dto.username == ""

    # Clean up override
    del app.dependency_overrides[get_get_calibrations_by_tag_use_case]


# Use Case 5: Query Tags Associated with a Calibration
@pytest.mark.asyncio
async def test_uc5_get_tags_for_calibration_success(
    async_client: AsyncClient,
    mock_get_tags_use_case: AsyncMock,
):
    """Tests GET /calibrations/{id}/tags success."""
    # Arrange
    test_cal_id = uuid4()
    expected_tags = ["tag1", "tag_foo"]
    mock_get_tags_use_case.execute.return_value = GetTagsForCalibrationOutput(
        tag_names=expected_tags
    )
    app.dependency_overrides[get_get_tags_for_calibration_use_case] = (
        lambda: mock_get_tags_use_case
    )

    # Act
    response = await async_client.get(f"/calibrations/{test_cal_id}/tags")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert response_data == expected_tags
    mock_get_tags_use_case.execute.assert_awaited_once()
    # Verify input DTO passed to use case
    call_args, _ = mock_get_tags_use_case.execute.call_args
    input_dto = call_args[0]
    assert isinstance(input_dto, GetTagsForCalibrationInput)
    assert input_dto.calibration_id == test_cal_id

    # Clean up override
    del app.dependency_overrides[get_get_tags_for_calibration_use_case]
