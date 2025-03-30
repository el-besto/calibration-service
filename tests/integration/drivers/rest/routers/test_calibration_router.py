# from unittest.mock import AsyncMock
# from uuid import uuid4
#
# import pytest
# from httpx import AsyncClient
#
# from src.application.use_cases.calibrations.add_calibration_use_case import (
#     AddCalibrationInput,
#     AddCalibrationOutput,
#     AddCalibrationUseCase,
# )
# from src.drivers.rest.dependencies import (
#     get_add_calibration_use_case,  # Import the dependency getter
# )
# from src.drivers.rest.main import app  # Import the FastAPI app instance
#
# # Mark all tests in this module as async and use the anyio backend
# pytestmark = [pytest.mark.asyncio, pytest.mark.anyio]
#
#
# @pytest.fixture
# def mock_add_calibration_use_case() -> AsyncMock:
#     """Fixture for a mocked AddCalibrationUseCase."""
#     return AsyncMock(spec=AddCalibrationUseCase)
#
#
# async def test_create_calibration_success(
#     async_client: AsyncClient,  # Use the client from conftest
#     mock_add_calibration_use_case: AsyncMock,  # Use the local mock fixture
# ):
#     """
#     Test POST /calibrations successfully creates a calibration.
#     """
#     # --- Arrange ---
#     calibration_data = {
#         "calibration_type": "offset",
#         "value": 1.23,
#         "timestamp": "2024-01-01T10:00:00Z",
#         "username": "test.user",
#     }
#     expected_calibration_id = uuid4()
#
#     # Configure the mock use case
#     mock_output = AddCalibrationOutput(calibration_id=expected_calibration_id)
#     # The controller calls the use case instance directly (if it implements __call__)
#     # or its .execute() method. Let's assume .execute() for now, based on other use cases.
#     # If this fails, we'll check the AddCalibrationUseCase implementation.
#     mock_add_calibration_use_case.execute.return_value = mock_output
#
#     # Override the dependency *for this test* to inject the mock use case
#     app.dependency_overrides[get_add_calibration_use_case] = (
#         lambda: mock_add_calibration_use_case
#     )
#
#     # --- Act ---
#     response = await async_client.post("/calibrations", json=calibration_data)
#
#     # --- Assert ---
#     # Check HTTP status code (e.g., 201 Created or 200 OK)
#     # Assuming 201 based on typical REST practices for creation
#     assert response.status_code == 201
#
#     # Check response body
#     response_data = response.json()
#     assert "calibration_id" in response_data
#     assert response_data["calibration_id"] == str(
#         expected_calibration_id
#     )  # IDs are often returned as strings
#
#     # Check that the use case mock was called correctly
#     mock_add_calibration_use_case.execute.assert_awaited_once()
#     call_args = mock_add_calibration_use_case.execute.call_args[0][0]
#     assert isinstance(call_args, AddCalibrationInput)
#     assert call_args.calibration_type == calibration_data["calibration_type"]
#     assert call_args.value == calibration_data["value"]
#     assert call_args.timestamp_str == calibration_data["timestamp"]
#     assert call_args.username == calibration_data["username"]
#
#     # --- Cleanup ---
#     # VERY IMPORTANT: Remove the dependency override after the test
#     del app.dependency_overrides[get_add_calibration_use_case]
