from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from src.drivers.rest.dependencies import (
    get_add_bulk_tags_to_calibration_controller,
    get_create_tag_controller,
    get_get_calibrations_by_tag_controller,
    get_list_tags_controller,
)
from src.drivers.rest.schemas.calibration_schemas import CalibrationReadResponse
from src.drivers.rest.schemas.tag_schemas import (
    BulkAddTagsRequest,
    BulkAddTagsResponse,
    TagCreateRequest,
    TagListResponse,
    TagResponse,
)
from src.entities.exceptions import (
    DatabaseOperationError,
    InputParseError,
    NotFoundError,
)
from src.interface_adapters.controllers.tags.add_bulk_tags_to_calibration_controller import (
    AddBulkTagsToCalibrationController,
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


# --- Association Routes ---


@router.post(
    "/calibrations/{calibration_id}/tags:bulk",
    response_model=BulkAddTagsResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk associate tags with a calibration",
    tags=["Tag Associations"],
    include_in_schema=False,
)
async def bulk_add_tags_to_calibration_endpoint(
    calibration_id: UUID,
    request: BulkAddTagsRequest,
    controller: AddBulkTagsToCalibrationController = Depends(
        get_add_bulk_tags_to_calibration_controller
    ),
) -> BulkAddTagsResponse:
    """API endpoint to bulk associate existing tags with an existing calibration."""
    try:
        return await controller.add_bulk_tags_to_calibration(calibration_id, request)
    except InputParseError as e:
        logger.warning(f"Input error bulk adding tags to {calibration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except NotFoundError as e:
        logger.warning(
            f"Not found error bulk associating tags with cal {calibration_id}: {e}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DatabaseOperationError as e:
        logger.error(f"DB error bulk associating tags with cal {calibration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error creating associations.",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error bulk associating tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e


@router.get(
    "/{tag_name}/calibrations",
    response_model=list[CalibrationReadResponse],
    summary="Retrieve calibrations by tag at a specific time",
    tags=["Tag Associations"],
    include_in_schema=False,
)
async def get_calibrations_by_tag_endpoint(
    tag_name: str,
    timestamp: datetime | None = None,
    username: str | None = None,
    controller: GetCalibrationsByTagController = Depends(
        get_get_calibrations_by_tag_controller
    ),
) -> list[CalibrationReadResponse]:
    """API endpoint to retrieve calibrations associated with a tag at a given timestamp.

    - **tag_name**: Name of the tag to search for.
    - **timestamp**: Optional ISO 8601 timestamp. Filters calibrations tagged at or before this time
                    and not untagged before this time. Defaults to the current UTC time if not provided.
    - **username**: Optional filter by username.
    """
    try:
        # Default to current UTC time if timestamp is not provided
        resolved_timestamp = timestamp if timestamp is not None else datetime.now(UTC)

        return await controller.get_calibrations_by_tag(
            tag_name=tag_name,
            timestamp=resolved_timestamp,
            username=username,
        )
    except NotFoundError as e:
        logger.warning(
            f"Not found error getting calibrations for tag '{tag_name}': {e}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DatabaseOperationError as e:
        logger.error(f"DB error getting calibrations for tag '{tag_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving calibrations.",
        ) from e
    except Exception as e:
        logger.exception(
            f"Unexpected error getting calibrations for tag '{tag_name}': {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e
