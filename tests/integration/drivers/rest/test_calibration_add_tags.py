# import uuid
# from typing import Any
#
# import pytest
# from fastapi import status
# from httpx import AsyncClient
#
# from src.domain.value_objects.calibration_type import CalibrationType
# from src.drivers.rest.dependencies import get_add_calibration_tag_use_case
# from src.drivers.rest.main import app
# from src.application.use_cases.exceptions import (
#     # CalibrationConflictError,
#     CalibrationNotFoundError,
# )
#
# calibration_id = uuid.uuid4()
# url = f"/calibrations/{calibration_id}/tags"
# calibration_type = CalibrationType.gain
# username = "angelo"
# payload = {"name": "tag 1", "action": "nothing"}
#
#
# @pytest.mark.parametrize(
#     "exception, status_code",
#     ((CalibrationNotFoundError(calibration_id), status.HTTP_404_NOT_FOUND),),
# )
# async def test_add_calibration_tag_with_exceptions(
#     async_client: AsyncClient, exception: Exception, status_code: int
# ):
#     class MockUseCase:
#         async def __call__(self, *args: Any, **kwargs: Any) -> None:
#             raise exception
#
#     app.dependency_overrides[get_add_calibration_tag_use_case] = MockUseCase
#
#     response = await async_client.post(url, json=payload)
#     assert response.status_code == status_code
#     assert response.json() == {"message": str(exception)}
#
#
# async def test_add_calibration_tag_success(async_client: AsyncClient):
#     class MockUseCase:
#         async def __call__(self, *args: Any, **kwargs: Any) -> None:
#             pass
#
#     app.dependency_overrides[get_add_calibration_tag_use_case] = MockUseCase
#     response = await async_client.post(url, json=payload)
#     assert response.status_code == status.HTTP_204_NO_CONTENT
