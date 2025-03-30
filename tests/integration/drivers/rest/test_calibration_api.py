from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from entities.models.calibration import Calibration, CalibrationType, Measurement
from entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.application.dtos.get_tags_for_calibration_dtos import (
    GetTagsForCalibrationInput,
    GetTagsForCalibrationOutput,
)
from src.application.use_cases.calibrations.add_calibration_use_case import (
    AddCalibrationInput,
    AddCalibrationOutput,
    AddCalibrationUseCase,
)
from src.application.use_cases.calibrations.get_tags_for_calibration import (
    GetTagsForCalibrationUseCase,
)
from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,  # Add exception
)
from src.drivers.rest.dependencies import (
    get_add_calibration_use_case,  # Import the dependency getter
    get_get_tags_for_calibration_use_case,
)
from src.drivers.rest.main import app  # Import the FastAPI app instance
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.calibration import Calibration  # Add Calibration import

# Mark all tests in this module as async and use the anyio backend
pytestmark = [pytest.mark.asyncio, pytest.mark.anyio]


@pytest.fixture
def mock_add_calibration_use_case() -> AsyncMock:
    """Fixture for a mocked AddCalibrationUseCase."""
    # Ensure the mock supports being called directly
    mock = AsyncMock(spec=AddCalibrationUseCase)
    # If __call__ is the execution method, mocking the instance directly works.
    # If execute exists, we might need mock.execute = AsyncMock()
    return mock


@pytest.fixture
def sample_created_calibration() -> Calibration:
    test_cal_id = uuid4()
    return Calibration(
        id=test_cal_id,
        measurement=Measurement(value=1.23, type=CalibrationType.offset),
        timestamp=Iso8601Timestamp(datetime.now(UTC).isoformat()),
        username="test.user",
        tags=[], # Assuming no tags initially
    )


async def test_create_calibration_success(
    async_client: AsyncClient,  # Use the client from conftest
    mock_add_calibration_use_case: AsyncMock,  # Use the local mock fixture
    sample_created_calibration: Calibration,  # Add fixture for result
):
    """
    Test POST /calibrations successfully creates a calibration.
    """
    # --- Arrange ---
    calibration_data = {
        "calibration_type": "offset",
        "value": 1.23,
        "timestamp": "2024-01-01T10:00:00Z",
        "username": "test.user",
    }

    # Configure the mock use case
    mock_output = AddCalibrationOutput(created_calibration=sample_created_calibration)
    # The controller calls the use case instance directly (if it implements __call__)
    # or its .execute() method. Let's assume __call__ now based on errors.
    mock_add_calibration_use_case.return_value = mock_output  # Mock the call itself

    # Override the dependency *for this test* to inject the mock use case
    app.dependency_overrides[get_add_calibration_use_case] = (
        lambda: mock_add_calibration_use_case
    )

    # --- Act ---
    response = await async_client.post("/calibrations", json=calibration_data)

    # --- Assert ---
    # Check HTTP status code (e.g., 201 Created or 200 OK)
    # Assuming 201 based on typical REST practices for creation
    assert response.status_code == 201

    # Check response body
    response_data = response.json()
    assert "calibration_id" in response_data
    assert response_data["calibration_id"] == str(sample_created_calibration.id)

    # Check that the use case mock was called correctly
    mock_add_calibration_use_case.assert_awaited_once()  # Check the __call__
    call_args = mock_add_calibration_use_case.call_args[0][0]
    assert isinstance(call_args, AddCalibrationInput)
    assert call_args.calibration_type == calibration_data["calibration_type"]
    assert call_args.value == calibration_data["value"]
    assert call_args.timestamp_str == calibration_data["timestamp"]
    assert call_args.username == calibration_data["username"]

    # --- Cleanup ---
    # VERY IMPORTANT: Remove the dependency override after the test
    del app.dependency_overrides[get_add_calibration_use_case]


async def test_create_calibration_invalid_input(
    async_client: AsyncClient,
):
    """
    Test POST /calibrations with invalid input data (e.g., missing field).
    """
    # --- Arrange ---
    invalid_calibration_data = {
        # Missing "calibration_type"
        "value": 1.23,
        "timestamp": "2024-01-01T10:00:00Z",
        "username": "test.user",
    }

    # --- Act ---
    response = await async_client.post("/calibrations", json=invalid_calibration_data)

    # --- Assert ---
    # FastAPI should return 422 for validation errors
    assert response.status_code == 422
    # Optionally check the detail message if needed
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    # Check for the specific missing field error structure
    found_error = False
    for item in response_data["detail"]:
        if (
            item.get("loc") == ["body", "calibration_type"]
            and item.get("type") == "missing"
        ):
            found_error = True
            break
    assert found_error, (
        f"Missing field error for 'calibration_type' not found in detail: {response_data['detail']}"
    )


async def test_create_calibration_use_case_error(
    async_client: AsyncClient,
    mock_add_calibration_use_case: AsyncMock,
):
    """
    Test POST /calibrations when the use case raises an error.
    """
    # --- Arrange ---
    calibration_data = {
        "calibration_type": "gain",
        "value": 9.99,
        "timestamp": "2024-01-02T11:00:00Z",
        "username": "error.user",
    }

    # Configure the mock use case to raise an error on __call__
    mock_add_calibration_use_case.side_effect = DatabaseOperationError(
        "DB write failed"
    )  # Set on __call__

    # Override the dependency
    app.dependency_overrides[get_add_calibration_use_case] = (
        lambda: mock_add_calibration_use_case
    )

    # --- Act ---
    response = await async_client.post("/calibrations", json=calibration_data)

    # --- Assert ---
    # Check for appropriate error status code (e.g., 500 or a specific mapped code)
    # Let's assume a generic 500 for now, as DatabaseOperationError might not be specifically handled
    # by the default exception handlers in this router/controller yet.
    # We might refine this later if specific exception handling is added.
    assert response.status_code == 500
    # Check response body for generic error message (depends on exception handlers)
    response_data = response.json()
    assert "detail" in response_data
    # assert response_data["detail"] == "Internal Server Error" # Or a more specific message

    # Check that the use case mock was still called
    mock_add_calibration_use_case.assert_awaited_once()  # Check __call__

    # --- Cleanup ---
    del app.dependency_overrides[get_add_calibration_use_case]


@pytest.fixture
def mock_get_tags_use_case() -> AsyncMock:
    """Fixture for a mocked GetTagsForCalibrationUseCase."""
    mock = AsyncMock(spec=GetTagsForCalibrationUseCase)
    # Assume .execute() based on unit tests
    mock.execute = AsyncMock()
    return mock


# Add these tests
async def test_get_tags_for_calibration_success(
    async_client: AsyncClient,
    mock_get_tags_use_case: AsyncMock,
):
    """
    Test GET /calibrations/{id}/tags successfully (Use Case 5).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    test_timestamp_str = "2024-02-15T12:00:00Z"
    expected_tags = ["tag_alpha", "tag_beta"]

    mock_output = GetTagsForCalibrationOutput(tag_names=expected_tags)
    mock_get_tags_use_case.execute.return_value = mock_output

    app.dependency_overrides[get_get_tags_for_calibration_use_case] = (
        lambda: mock_get_tags_use_case
    )

    # --- Act ---
    response = await async_client.get(
        f"/calibrations/{test_cal_id}/tags", params={"timestamp": test_timestamp_str}
    )

    # --- Assert ---
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    # Assuming the presenter returns the list directly
    assert sorted(response_data) == sorted(expected_tags)  # Compare sorted lists

    mock_get_tags_use_case.execute.assert_awaited_once()
    call_args = mock_get_tags_use_case.execute.call_args[0][0]
    assert isinstance(call_args, GetTagsForCalibrationInput)
    assert call_args.calibration_id == test_cal_id
    assert (
        call_args.timestamp.isoformat().replace("+00:00", "Z") == test_timestamp_str
    )  # Check parsed timestamp with Z format

    # --- Cleanup ---
    del app.dependency_overrides[get_get_tags_for_calibration_use_case]


async def test_get_tags_for_calibration_no_tags(
    async_client: AsyncClient,
    mock_get_tags_use_case: AsyncMock,
):
    """
    Test GET /calibrations/{id}/tags when no tags are associated (Use Case 5).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    test_timestamp_str = "2024-02-15T13:00:00Z"
    expected_tags = []  # Empty list

    mock_output = GetTagsForCalibrationOutput(tag_names=expected_tags)
    mock_get_tags_use_case.execute.return_value = mock_output

    app.dependency_overrides[get_get_tags_for_calibration_use_case] = (
        lambda: mock_get_tags_use_case
    )

    # --- Act ---
    response = await async_client.get(
        f"/calibrations/{test_cal_id}/tags", params={"timestamp": test_timestamp_str}
    )

    # --- Assert ---
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert response_data == expected_tags  # Should be an empty list

    mock_get_tags_use_case.execute.assert_awaited_once()
    call_args = mock_get_tags_use_case.execute.call_args[0][0]
    assert call_args.calibration_id == test_cal_id

    # --- Cleanup ---
    del app.dependency_overrides[get_get_tags_for_calibration_use_case]


async def test_get_tags_for_calibration_not_found(
    async_client: AsyncClient,
    mock_get_tags_use_case: AsyncMock,
):
    """
    Test GET /calibrations/{id}/tags when calibration ID is not found (Use Case 5).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    test_timestamp_str = "2024-02-15T14:00:00Z"
    error_message = f"Calibration '{test_cal_id}' not found."

    # Configure use case to raise CalibrationNotFoundError
    mock_get_tags_use_case.execute.side_effect = CalibrationNotFoundError(error_message)

    app.dependency_overrides[get_get_tags_for_calibration_use_case] = (
        lambda: mock_get_tags_use_case
    )

    # --- Act ---
    response = await async_client.get(
        f"/calibrations/{test_cal_id}/tags", params={"timestamp": test_timestamp_str}
    )

    # --- Assert ---
    # Assuming NotFoundError from use case maps to 404
    assert response.status_code == 404
    response_data = response.json()
    assert "detail" in response_data
    assert error_message in response_data["detail"]

    mock_get_tags_use_case.execute.assert_awaited_once()

    # --- Cleanup ---
    del app.dependency_overrides[get_get_tags_for_calibration_use_case]


async def test_get_tags_for_calibration_invalid_timestamp(
    async_client: AsyncClient,
):
    """
    Test GET /calibrations/{id}/tags with invalid timestamp format (Use Case 5).
    """
    # --- Arrange ---
    test_cal_id = uuid4()
    invalid_timestamp_str = "not-a-valid-timestamp"

    # No need to mock use case, error should happen during DTO validation in controller

    # --- Act ---
    response = await async_client.get(
        f"/calibrations/{test_cal_id}/tags", params={"timestamp": invalid_timestamp_str}
    )

    # --- Assert ---
    assert response.status_code == 422 # Correct status code to 422
    response_data = response.json()
    assert "detail" in response_data
    # Check for specific validation error message from Pydantic/FastAPI
    assert any(
        "Input should be a valid datetime" in error["msg"]
        for error in response_data["detail"]
    )
