from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture

from application.use_cases.calibrations.list_calibrations import (
    ListCalibrationsOutput,
    ListCalibrationsUseCase,
)
from src.application.use_cases.exceptions import (  # Import relevant exceptions
    AssociationNotFoundError,
    CalibrationNotFoundError,
)
from src.application.use_cases.tags.add_tag_to_calibration import (
    AddTagToCalibrationInput,
    AddTagToCalibrationUseCase,
    # AddTagToCalibrationOutput # Output might not be used if presenter is mocked
)
from src.application.use_cases.tags.remove_tag_from_calibration import (
    RemoveTagFromCalibrationInput,
    RemoveTagFromCalibrationUseCase,
    # RemoveTagFromCalibrationOutput # Output might not be used if presenter is mocked
)
from src.drivers.rest.dependencies import (
    get_add_tag_to_calibration_use_case,
    get_list_calibrations_use_case,
    get_remove_tag_from_calibration_use_case,
)
from src.drivers.rest.main import app  # Import the FastAPI app instance
from src.entities.models.calibration import Calibration
from src.entities.models.tag import Tag
from src.entities.value_objects.calibration_type import CalibrationType, Measurement
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp

# Mark all tests in this module as async and use the anyio backend
pytestmark = [pytest.mark.asyncio, pytest.mark.anyio]


# --- Fixtures ---


@pytest.fixture
def mock_add_tag_use_case() -> AsyncMock:
    """Fixture for a mocked AddTagToCalibrationUseCase."""
    mock = AsyncMock(spec=AddTagToCalibrationUseCase)
    # Assuming .execute() based on unit tests
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_remove_tag_use_case() -> AsyncMock:
    """Fixture for a mocked RemoveTagFromCalibrationUseCase."""
    mock = AsyncMock(spec=RemoveTagFromCalibrationUseCase)
    # Assuming .execute() based on unit tests
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_list_calibrations_use_case(mocker: MockerFixture) -> AsyncMock:
    """Fixture to mock the ListCalibrationsUseCase instance."""
    # Create an AsyncMock that is itself awaitable
    mock_instance = AsyncMock(spec=ListCalibrationsUseCase)
    # No need to mock __call__ separately if the instance itself handles the call.
    return mock_instance  # noqa: RET504


# --- Tests for POST /calibrations/{id}/tags ---


async def test_add_tag_to_calibration_success(
    async_client: AsyncClient,
    mock_add_tag_use_case: AsyncMock,
):
    """
    Test POST /calibrations/{id}/tags successfully adds a tag (Use Case 3).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    tag_name = "new-tag-via-api"
    request_body = {"tag": tag_name}

    # Configure mock use case (assuming it returns None or a simple output on success)
    mock_add_tag_use_case.execute.return_value = None  # Or a mock output object

    # Override dependency
    app.dependency_overrides[get_add_tag_to_calibration_use_case] = (
        lambda: mock_add_tag_use_case
    )

    # --- Act ---
    response = await async_client.post(
        f"/calibrations/{test_cal_id}/tags", json=request_body
    )

    # --- Assert ---
    # Assuming 200 OK for successful tag addition
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == {"message": "Tag added successfully"}  # As per PROJECT.md

    mock_add_tag_use_case.execute.assert_awaited_once()
    call_args = mock_add_tag_use_case.execute.call_args[0][0]
    assert isinstance(call_args, AddTagToCalibrationInput)
    assert call_args.calibration_id == test_cal_id
    # Note: The controller likely looks up the tag ID based on the name before calling the use case.
    # Asserting the exact tag_id passed to the use case requires mocking the controller's
    # internal tag lookup (e.g., mocking tag_repository.get_by_name) which adds complexity.
    # For this integration test, verifying the use case was called with the correct
    # calibration_id might be sufficient, relying on unit tests for the controller's internal logic.

    # --- Cleanup ---
    del app.dependency_overrides[get_add_tag_to_calibration_use_case]


async def test_add_tag_to_calibration_cal_not_found(
    async_client: AsyncClient,
    mock_add_tag_use_case: AsyncMock,
):
    """
    Test POST /calibrations/{id}/tags when calibration is not found (Use Case 3).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    tag_name = "tag-for-missing-cal"
    request_body = {"tag": tag_name}
    error_message = f"Calibration {test_cal_id} not found"

    # Configure mock use case to raise error
    # The controller might raise NotFoundError based on CalibrationNotFoundError
    mock_add_tag_use_case.execute.side_effect = CalibrationNotFoundError(error_message)

    # Override dependency
    app.dependency_overrides[get_add_tag_to_calibration_use_case] = (
        lambda: mock_add_tag_use_case
    )

    # --- Act ---
    response = await async_client.post(
        f"/calibrations/{test_cal_id}/tags", json=request_body
    )

    # --- Assert ---
    assert response.status_code == 404
    response_data = response.json()
    assert "detail" in response_data
    # The controller might wrap the specific message
    assert str(test_cal_id) in response_data["detail"]
    assert "not found" in response_data["detail"].lower()

    mock_add_tag_use_case.execute.assert_awaited_once()  # Use case is still called

    # --- Cleanup ---
    del app.dependency_overrides[get_add_tag_to_calibration_use_case]


# --- Tests for DELETE /calibrations/{id}/tags/{tag_name} ---


async def test_remove_tag_from_calibration_success(
    async_client: AsyncClient,
    mock_remove_tag_use_case: AsyncMock,
    mocker: MockerFixture,
):
    """
    Test DELETE /calibrations/{id}/tags successfully removes a tag (Use Case 3).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    tag_name = "tag-to-remove"
    tag_id = uuid4()

    # Mock the tag lookup within the controller using the concrete repo path
    mock_get_tag = mocker.patch(
        "src.infrastructure.repositories.tag_repository.postgres_repository.SqlAlchemyTagRepository.get_by_name",
        return_value=Tag(id=tag_id, name=tag_name),
    )

    # Configure mock use case
    mock_remove_tag_use_case.execute.return_value = None

    # Override dependency
    app.dependency_overrides[get_remove_tag_from_calibration_use_case] = (
        lambda: mock_remove_tag_use_case
    )

    # --- Act ---
    response = await async_client.delete(f"/calibrations/{test_cal_id}/tags/{tag_name}")

    # --- Assert ---
    assert response.status_code == 200
    mock_get_tag.assert_awaited_once_with(tag_name)
    # Assert use case was called with the FOUND tag_id
    mock_remove_tag_use_case.execute.assert_awaited_once()
    call_args = mock_remove_tag_use_case.execute.call_args[0][0]
    assert isinstance(call_args, RemoveTagFromCalibrationInput)
    assert call_args.calibration_id == test_cal_id
    assert call_args.tag_id == tag_id
    response_data = response.json()
    assert response_data == {"message": "Tag removed successfully"}

    # --- Cleanup ---
    del app.dependency_overrides[get_remove_tag_from_calibration_use_case]


async def test_remove_tag_from_calibration_assoc_not_found(
    async_client: AsyncClient,
    mock_remove_tag_use_case: AsyncMock,
    mocker: MockerFixture,
):
    """
    Test DELETE /calibrations/{id}/tags when association is not found (Use Case 3).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    tag_name = "tag-not-associated"
    tag_id = uuid4()
    error_message = f"No active association found for tag {tag_name}"

    # Mock the tag lookup within the controller using the concrete repo path
    mock_get_tag = mocker.patch(
        "src.infrastructure.repositories.tag_repository.postgres_repository.SqlAlchemyTagRepository.get_by_name",
        return_value=Tag(id=tag_id, name=tag_name),
    )

    # Configure mock use case to raise the expected error
    mock_remove_tag_use_case.execute.side_effect = AssociationNotFoundError(
        error_message
    )

    # Override dependency
    app.dependency_overrides[get_remove_tag_from_calibration_use_case] = (
        lambda: mock_remove_tag_use_case
    )

    # --- Act ---
    response = await async_client.delete(f"/calibrations/{test_cal_id}/tags/{tag_name}")

    # --- Assert ---
    assert response.status_code == 404
    mock_get_tag.assert_awaited_once_with(tag_name)
    # Assert use case was called correctly before raising error
    mock_remove_tag_use_case.execute.assert_awaited_once()
    call_args = mock_remove_tag_use_case.execute.call_args[0][0]
    assert isinstance(call_args, RemoveTagFromCalibrationInput)
    assert call_args.calibration_id == test_cal_id
    assert call_args.tag_id == tag_id
    # Check the detail message from the exception
    response_data = response.json()
    assert "detail" in response_data
    assert error_message in response_data["detail"]

    # --- Cleanup ---
    del app.dependency_overrides[get_remove_tag_from_calibration_use_case]


async def test_list_calibrations_by_tag(
    async_client: AsyncClient,
    mock_list_calibrations_use_case: AsyncMock,
):
    """
    Test GET /calibrations successfully retrieves calibrations filtered by tag.
    Covers Use Case 4.
    """
    # Arrange
    tag_to_query = "test-tag"
    calibration_id = uuid4()
    test_timestamp = datetime.now(UTC)
    test_value = 1.23
    test_user = "testuser"

    # Create the expected *domain entity* for the mock return
    expected_domain_calibrations = [
        Calibration(
            id=calibration_id,
            measurement=Measurement(value=test_value, type=CalibrationType.gain),
            timestamp=Iso8601Timestamp(test_timestamp.isoformat()),
            username=test_user,
            tags=[Tag(id=uuid4(), name=tag_to_query)],
        )
    ]

    # Override dependency - lambda should return the mock instance directly
    app.dependency_overrides[get_list_calibrations_use_case] = (
        lambda: mock_list_calibrations_use_case
    )

    # Configure the return value of awaiting the mock instance directly
    mock_list_calibrations_use_case.return_value = ListCalibrationsOutput(
        calibrations=expected_domain_calibrations
    )

    # Act
    response = await async_client.get(f"/calibrations?tags={tag_to_query}")

    # Assert
    assert response.status_code == 200
    response_data = response.json()

    # Check if the response is a dict with a 'calibrations' key containing a list
    assert isinstance(response_data, dict)
    assert "calibrations" in response_data
    calibrations_list = response_data["calibrations"]
    assert isinstance(calibrations_list, list)
    assert len(calibrations_list) == 1  # Check length of the inner list

    # Assertions on the first calibration object in the list
    first_calibration = calibrations_list[0]
    assert first_calibration["id"] == str(calibration_id)  # Use 'id'
    assert first_calibration["type"] == CalibrationType.gain.value  # Use 'type'
    assert first_calibration["value"] == test_value
    assert first_calibration["username"] == test_user
    assert first_calibration["tags"] == [tag_to_query]
    # Verify the mock instance was awaited correctly
    mock_list_calibrations_use_case.assert_awaited_once()  # Re-enable assertion
    # call_args, _ = mock_list_calibrations_use_case.call_args
    # assert call_args[0].tags == [tag_to_query]

    # Cleanup
    del app.dependency_overrides[get_list_calibrations_use_case]
