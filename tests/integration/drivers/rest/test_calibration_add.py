# # Add these imports at the top of tests/integration/drivers/rest/test_calibration_api.py
# # (if they aren't already there from the POST /calibrations tests)
# from unittest.mock import AsyncMock
# from uuid import uuid4
#
# import pytest
# from httpx import AsyncClient
#
# from src.application.use_cases.calibrations.list_calibrations import (
#     ListCalibrationsInput,
#     ListCalibrationsOutput,
#     ListCalibrationsUseCase,
# )
# from src.drivers.rest.dependencies import (
#     get_list_calibrations_use_case,  # Import dependency getter
# )
# from src.drivers.rest.main import app  # Import the FastAPI app instance
# from src.entities.exceptions import DatabaseOperationError  # Import exception
# from src.entities.models.calibration import (  # Needed for sample data
#     Calibration,
#     Measurement,
# )
# from src.entities.value_objects.calibration_type import (
#     CalibrationType,  # Needed for sample data
# )
# from src.entities.value_objects.iso_8601_timestamp import (
#     Iso8601Timestamp,  # Needed for sample data
# )
#
#
# # Add this fixture to the file
# @pytest.fixture
# def mock_list_calibrations_use_case() -> AsyncMock:
#     """Fixture for a mocked ListCalibrationsUseCase."""
#     mock = AsyncMock(spec=ListCalibrationsUseCase)
#     # Assuming this use case might also use __call__ based on others
#     # If tests fail with AttributeError: Mock object has no attribute 'execute',
#     # change mocking below from .return_value/.side_effect to .execute.return_value/.execute.side_effect
#     return mock
#
#
# # Add these test functions to the file
# async def test_list_calibrations_no_filters(
#     async_client: AsyncClient,
#     mock_list_calibrations_use_case: AsyncMock,
# ):
#     """
#     Test GET /calibrations successfully with no filters (Use Case 2).
#     """
#     # --- Arrange ---
#     # Create some sample Calibration data the use case should return
#     cal1 = Calibration(
#         id=uuid4(),
#         measurement=Measurement(value=1.0, type=CalibrationType.gain),
#         timestamp=Iso8601Timestamp("2023-10-26T10:00:00Z"),
#         username="user1",
#         tags=[],
#     )
#     cal2 = Calibration(
#         id=uuid4(),
#         measurement=Measurement(value=2.5, type=CalibrationType.offset),
#         timestamp=Iso8601Timestamp("2023-10-26T11:00:00Z"),
#         username="user2",
#         tags=[],
#     )
#     mock_output = ListCalibrationsOutput(calibrations=[cal1, cal2])
#     mock_list_calibrations_use_case.return_value = mock_output  # Mock __call__
#
#     app.dependency_overrides[get_list_calibrations_use_case] = (
#         lambda: mock_list_calibrations_use_case
#     )
#
#     # --- Act ---
#     response = await async_client.get("/calibrations")
#
#     # --- Assert ---
#     assert response.status_code == 200
#     response_data = response.json()
#     assert isinstance(response_data, list)
#     assert len(response_data) == 2
#     # Check structure of the first item (assuming presenter works)
#     assert response_data[0]["id"] == str(cal1.id)
#     assert response_data[0]["username"] == cal1.username
#     assert response_data[0]["calibration_type"] == cal1.measurement.type.value
#     assert response_data[0]["value"] == cal1.measurement.value
#     assert (
#         response_data[0]["timestamp"] == cal1.timestamp.isoformat()
#     )  # Check ISO format string
#
#     mock_list_calibrations_use_case.assert_awaited_once()
#     # Check that input DTO had None for filters
#     call_args = mock_list_calibrations_use_case.call_args[0][0]
#     assert isinstance(call_args, ListCalibrationsInput)
#     assert call_args.username is None
#     assert call_args.timestamp_str is None
#     assert call_args.calibration_type_str is None
#
#     # --- Cleanup ---
#     del app.dependency_overrides[get_list_calibrations_use_case]
#
#
# async def test_list_calibrations_with_filters(
#     async_client: AsyncClient,
#     mock_list_calibrations_use_case: AsyncMock,
# ):
#     """
#     Test GET /calibrations successfully with filters (Use Case 2).
#     """
#     # --- Arrange ---
#     # Sample data that *matches* the filters
#     cal_match = Calibration(
#         id=uuid4(),
#         measurement=Measurement(value=5.0, type=CalibrationType.offset),
#         timestamp=Iso8601Timestamp("2023-11-01T09:00:00Z"),
#         username="filteruser",
#         tags=[],
#     )
#     # Assume use case correctly filters and returns only the match
#     mock_output = ListCalibrationsOutput(calibrations=[cal_match])
#     mock_list_calibrations_use_case.return_value = mock_output  # Mock __call__
#
#     filters = {
#         "username": "filteruser",
#         "timestamp": "2023-11-01T09:00:00Z",
#         "calibration_type": "offset",  # Use valid enum string value
#     }
#
#     app.dependency_overrides[get_list_calibrations_use_case] = (
#         lambda: mock_list_calibrations_use_case
#     )
#
#     # --- Act ---
#     response = await async_client.get("/calibrations", params=filters)
#
#     # --- Assert ---
#     assert response.status_code == 200
#     response_data = response.json()
#     assert isinstance(response_data, list)
#     assert len(response_data) == 1
#     assert response_data[0]["id"] == str(cal_match.id)
#     assert response_data[0]["username"] == filters["username"]
#     assert response_data[0]["calibration_type"] == filters["calibration_type"]
#     assert (
#         response_data[0]["timestamp"] == filters["timestamp"]
#     )  # Timestamp matches filter
#
#     mock_list_calibrations_use_case.assert_awaited_once()
#     # Check that input DTO had correct filter values
#     call_args = mock_list_calibrations_use_case.call_args[0][0]
#     assert isinstance(call_args, ListCalibrationsInput)
#     assert call_args.username == filters["username"]
#     assert call_args.timestamp_str == filters["timestamp"]
#     assert call_args.calibration_type_str == filters["calibration_type"]
#
#     # --- Cleanup ---
#     del app.dependency_overrides[get_list_calibrations_use_case]
#
#
# async def test_list_calibrations_use_case_error(
#     async_client: AsyncClient,
#     mock_list_calibrations_use_case: AsyncMock,
# ):
#     """
#     Test GET /calibrations when the use case raises an error (Use Case 2).
#     """
#     # --- Arrange ---
#     mock_list_calibrations_use_case.side_effect = DatabaseOperationError("Read failed")
#
#     app.dependency_overrides[get_list_calibrations_use_case] = (
#         lambda: mock_list_calibrations_use_case
#     )
#
#     # --- Act ---
#     response = await async_client.get("/calibrations")
#
#     # --- Assert ---
#     assert response.status_code == 500  # Assuming generic handler
#     response_data = response.json()
#     assert "detail" in response_data
#     # Example: Check for a generic message if specific handler isn't set up
#     # assert "Internal server error" in response_data["detail"].lower()
#
#     mock_list_calibrations_use_case.assert_awaited_once()
#
#     # --- Cleanup ---
#     del app.dependency_overrides[get_list_calibrations_use_case]
#
#
# async def test_list_calibrations_invalid_filter_value(
#     async_client: AsyncClient,
# ):
#     """
#     Test GET /calibrations with an invalid filter value (Use Case 2).
#     """
#     # --- Arrange ---
#     filters = {
#         "calibration_type": "invalid-enum-value",
#     }
#     # No need to mock use case, error should happen in controller/DTO validation
#
#     # --- Act ---
#     response = await async_client.get("/calibrations", params=filters)
#
#     # --- Assert ---
#     # Expect 400 Bad Request as controller maps InputParseError from DTO
#     assert response.status_code == 400
#     response_data = response.json()
#     assert "detail" in response_data
#     assert "Invalid filter value" in response_data["detail"]
#     assert (
#         "'invalid-enum-value' is not a valid CalibrationType" in response_data["detail"]
#     )
