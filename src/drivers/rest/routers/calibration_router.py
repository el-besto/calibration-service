from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from src.application.use_cases.exceptions import UseCaseError
from src.drivers.rest.dependencies import (
    get_add_calibration_controller,
    get_add_tag_to_calibration_controller,
    get_get_tags_for_calibration_controller,
    get_list_calibrations_controller,
    get_remove_tag_from_calibration_controller,
)
from src.drivers.rest.schemas.calibration_schemas import (
    CalibrationCreateRequest,
    CalibrationCreateResponse,
    CalibrationListResponse,
)
from src.drivers.rest.schemas.tag_schemas import (
    TagOperationRequest,
    TagOperationResponse,
)
from src.entities.exceptions import (
    DatabaseOperationError,
    InputParseError,
    NotFoundError,
)
from src.interface_adapters.controllers.calibrations.add_calibration_controller import (
    AddCalibrationController,
)
from src.interface_adapters.controllers.calibrations.get_tags_for_calibration_controller import (
    GetTagsForCalibrationController,
)
from src.interface_adapters.controllers.calibrations.list_calibrations_controller import (
    ListCalibrationsController,
)
from src.interface_adapters.controllers.tags.add_tag_to_calibration_controller import (
    AddTagToCalibrationController,
)
from src.interface_adapters.controllers.tags.remove_tag_from_calibration_controller import (
    RemoveTagFromCalibrationController,
)

router = APIRouter(prefix="/calibrations", tags=["Calibrations"])


@router.post(
    "",  # Maps to POST /calibrations
    response_model=CalibrationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="1. Create a new calibration",
)
async def create_calibration_endpoint(
    request: CalibrationCreateRequest,
    controller: Annotated[
        AddCalibrationController, Depends(get_add_calibration_controller)
    ],
) -> CalibrationCreateResponse:
    """API endpoint to create a new calibration measurement."""
    try:
        # Delegate to the controller method
        return await controller.create_calibration(request)
    except InputParseError as e:
        logger.warning(f"Input parse error creating calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DatabaseOperationError as e:
        logger.error(f"Database error creating calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while creating the calibration.",
        ) from e
    except UseCaseError as e:
        logger.error(f"Use case error creating calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal application error occurred.",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error creating calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e


@router.get(
    "",
    response_model=CalibrationListResponse,
    summary="2. List calibrations by filter and 4. Retrieve Calibrations by Tag",
)
async def list_calibrations_endpoint(
    controller: Annotated[
        ListCalibrationsController, Depends(get_list_calibrations_controller)
    ],
    username: str | None = Query(None, description="Filter by username"),
    timestamp: str | None = Query(
        None, description="Filter by exact ISO 8601 timestamp"
    ),
    calibration_type: str | None = Query(
        None, description="Filter by calibration type"
    ),
) -> CalibrationListResponse:
    """API endpoint to list calibrations, optionally filtering by query parameters."""
    try:
        return await controller.list_calibrations(
            username=username, timestamp=timestamp, calibration_type=calibration_type
        )
    except InputParseError as e:
        logger.warning(f"Invalid filter value provided for listing calibrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DatabaseOperationError as e:
        logger.error(f"Database error listing calibrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while listing calibrations.",
        ) from e
    except UseCaseError as e:
        logger.error(f"Use case error listing calibrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal application error occurred.",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error listing calibrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e


@router.get(
    "/{calibration_id}/tags",
    response_model=list[str],
    summary="5. Query Tags Associated with a Calibration at a specific time",
)
async def get_tags_for_calibration_endpoint(
    calibration_id: UUID,
    controller: Annotated[
        GetTagsForCalibrationController,
        Depends(get_get_tags_for_calibration_controller),
    ],
    timestamp: datetime | None = Query(
        None, description="Optional ISO 8601 timestamp. Defaults to current UTC time."
    ),
) -> list[str]:
    """API endpoint to list tags associated with a calibration, optionally at a given time."""
    try:
        # Default to current UTC time if timestamp is not provided
        resolved_timestamp = timestamp if timestamp is not None else datetime.now(UTC)

        return await controller.get_tags_for_calibration(
            calibration_id=calibration_id, timestamp=resolved_timestamp
        )
    except NotFoundError as e:
        logger.warning(f"Not found error getting tags for cal {calibration_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DatabaseOperationError as e:
        logger.error(f"DB error getting tags for cal {calibration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving tags.",
        ) from e
    except UseCaseError as e:
        logger.error(f"Use case error getting tags for cal {calibration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal application error occurred.",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error getting tags for cal {calibration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e


@router.post(
    "/{calibration_id}/tags",
    response_model=TagOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="3a. Add a tag to a Calibration by name",
)
async def add_tag_to_calibration_endpoint(
    calibration_id: UUID,
    request: TagOperationRequest,
    controller: AddTagToCalibrationController = Depends(
        get_add_tag_to_calibration_controller
    ),
) -> TagOperationResponse:
    """API endpoint to associate an existing or new tag (by name) with a calibration."""
    try:
        return await controller.add_tag_to_calibration(calibration_id, request)
    except NotFoundError as e:
        logger.warning(f"Not found error adding tag to cal {calibration_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DatabaseOperationError as e:
        logger.error(f"DB error adding tag to cal {calibration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error adding tag association.",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error adding tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e


@router.delete(
    "/{calibration_id}/tags/{tag_name}",
    response_model=TagOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="3b. remove a tag",
)
async def remove_tag_from_calibration_path_endpoint(
    calibration_id: UUID,
    tag_name: str,
    controller: RemoveTagFromCalibrationController = Depends(
        get_remove_tag_from_calibration_controller
    ),
) -> TagOperationResponse:
    """API endpoint to disassociate a tag (by name) from a calibration."""
    try:
        request = TagOperationRequest(tag=tag_name)
        return await controller.remove_tag_from_calibration(calibration_id, request)
    except NotFoundError as e:
        logger.warning(f"Not found error removing tag from cal {calibration_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DatabaseOperationError as e:
        logger.error(f"DB error removing tag from cal {calibration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error removing tag association.",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error removing tag association: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e
