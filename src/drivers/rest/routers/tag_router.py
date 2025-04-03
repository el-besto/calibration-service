from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from src.application.use_cases.exceptions import TagNotFoundError
from src.drivers.rest.dependencies import (
    get_create_tag_controller,
    get_get_calibrations_by_tag_controller,
    get_list_tags_controller,
)
from src.drivers.rest.schemas.calibration_schemas import (
    CalibrationListResponse,
)
from src.drivers.rest.schemas.tag_schemas import (
    TagCreateRequest,
    TagListResponse,
    TagResponse,
)
from src.entities.exceptions import (
    DatabaseOperationError,
    InputParseError,
)
from src.interface_adapters.controllers.tags.create_tag_controller import (
    CreateTagController,
)
from src.interface_adapters.controllers.tags.get_calibrations_by_tag_controller import (
    GetCalibrationsByTagController,
)
from src.interface_adapters.controllers.tags.list_tags_controller import (
    ListTagsController,
)

# --- Router Definition ---

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
    include_in_schema=False,
)
async def create_tag_endpoint(
    request: TagCreateRequest,
    controller: CreateTagController = Depends(get_create_tag_controller),
) -> TagResponse:
    """API endpoint to create a new tag."""
    try:
        return await controller.create_tag(request)
    except InputParseError as e:
        logger.warning(f"Input error creating tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DatabaseOperationError as e:
        logger.error(f"DB error creating tag: {e}")
        # Check for specific duplicate name error message if needed
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error creating tag.",
        ) from e
    except Exception as e:
        logger.exception(
            f"Unexpected error creating tag: {e}"
        )  # Use exception for stacktrace
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e


@router.get(
    "", response_model=TagListResponse, summary="List all tags", include_in_schema=False
)
async def list_tags_endpoint(
    controller: ListTagsController = Depends(get_list_tags_controller),
) -> TagListResponse:
    """API endpoint to list all existing tags."""
    try:
        return await controller.list_all_tags()
    except DatabaseOperationError as e:
        logger.error(f"DB error listing tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error listing tags.",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error listing tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e


@router.get(
    "/{tag_name}/calibrations",
    response_model=CalibrationListResponse,
    summary="Get calibrations associated with a specific tag",
    include_in_schema=False,
)
async def get_calibrations_by_tag_endpoint(
    tag_name: str,
    controller: GetCalibrationsByTagController = Depends(
        get_get_calibrations_by_tag_controller
    ),
) -> CalibrationListResponse:
    """API endpoint to retrieve all calibrations associated with a specific tag."""
    try:
        return await controller.get_calibrations_by_tag(
            tag_name, timestamp=datetime.now(UTC), username=""
        )

    except TagNotFoundError as e:
        logger.warning(f"Tag not found for listing calibrations: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DatabaseOperationError as e:
        logger.error(f"DB error getting calibrations by tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving calibrations for tag.",
        ) from e
    except Exception as e:
        logger.exception(
            f"Unexpected error getting calibrations by tag '{tag_name}': {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e
