import os
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.repositories.tag_repository import TagRepository
from src.application.use_cases.calibrations.add_calibration_tags import (
    AddCalibrationTagUseCase,
)
from src.application.use_cases.calibrations.add_calibration_use_case import (
    AddCalibrationUseCase,
)
from src.application.use_cases.calibrations.get_tags_for_calibration import (
    GetTagsForCalibrationUseCase,
)
from src.application.use_cases.calibrations.list_calibrations import (
    ListCalibrationsUseCase,
)
from src.application.use_cases.tags.add_bulk_tags_to_calibration import (
    AddBulkTagsToCalibrationUseCase,
)
from src.application.use_cases.tags.add_tag_to_calibration import (
    AddTagToCalibrationUseCase,
)
from src.application.use_cases.tags.create_tag import CreateTagUseCase
from src.application.use_cases.tags.get_calibrations_by_tag import (
    GetCalibrationsByTagUseCase,
)
from src.application.use_cases.tags.list_tags import ListTagsUseCase
from src.application.use_cases.tags.remove_tag_from_calibration import (
    RemoveTagFromCalibrationUseCase,
)
from src.config.database import get_session
from src.infrastructure.repositories.calibration_repository.in_memory_repository import (
    InMemoryCalibrationRepository,
)
from src.infrastructure.repositories.calibration_repository.mongodb_repository import (
    MongoCalibrationRepository,
)
from src.infrastructure.repositories.calibration_repository.postgres_repository import (
    SqlAlchemyCalibrationRepository,
)
from src.infrastructure.repositories.tag_repository.mock_repository import (
    MockTagRepository,
)
from src.infrastructure.repositories.tag_repository.postgres_repository import (
    SqlAlchemyTagRepository,
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
from src.interface_adapters.controllers.tags.create_tag_controller import (
    CreateTagController,
)
from src.interface_adapters.controllers.tags.get_calibrations_by_tag_controller import (
    GetCalibrationsByTagController,
)
from src.interface_adapters.controllers.tags.list_tags_controller import (
    ListTagsController,
)
from src.interface_adapters.controllers.tags.remove_tag_from_calibration_controller import (
    RemoveTagFromCalibrationController,
)


## ############################# ##
## NOSQL CLIENT
## ############################# ##
@lru_cache
def get_mongo_client() -> AsyncIOMotorClient[Any]:
    """Get a MongoDB client instance.

    Returns:
        AsyncIOMotorClient: A MongoDB client for async operations.
    """
    # FIXME: read mongoURI from an env setting
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    logger.info(f"Connecting to MongoDB at {mongo_uri}")
    return AsyncIOMotorClient(mongo_uri)


## ############################# ##
## DI WRAPPERS FOR CALIBRATIONS
## ############################# ##


def get_calibration_repository(
    # Inject dependencies needed by *any* potential repository implementation
    session: Annotated[AsyncSession, Depends(get_session)],
    mongo_client: Annotated[AsyncIOMotorClient[Any], Depends(get_mongo_client)],
) -> CalibrationRepository:
    """Provides a CalibrationRepository instance based on REPOSITORY_TYPE env var.

    Injects dependencies required by the selected repository type.

    Returns:
        CalibrationRepository: An instance conforming to the repository interface.

    Raises:
        ValueError: If REPOSITORY_TYPE is not set or invalid.
    """
    repo_type = os.getenv("REPOSITORY_TYPE", "postgres").lower()

    if repo_type == "postgres":
        logger.info("Using PostgreSQL Repository")
        return SqlAlchemyCalibrationRepository(session)
    if repo_type == "mongo":
        logger.info("Using MongoDB Repository")
        return MongoCalibrationRepository(mongo_client)  # pyright: ignore [reportAbstractUsage]
    if repo_type == "mock":
        logger.info("Using Mock/In-Memory Repository")
        # Ensure MockCalibrationRepository is properly initialized if needed
        return InMemoryCalibrationRepository()  # pyright: ignore [reportAbstractUsage]
    logger.error(
        f"Invalid REPOSITORY_TYPE specified: {repo_type}. Choose postgres, mongo, or mock."
    )
    raise ValueError(
        f"Invalid REPOSITORY_TYPE: {repo_type}. Choose postgres, mongo, or mock."
    )


def get_add_calibration_use_case(
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
) -> AddCalibrationUseCase:
    """Get the use case for adding calibrations."""
    return AddCalibrationUseCase(calibration_repository)


def get_add_calibration_tag_use_case(
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
) -> AddCalibrationTagUseCase:
    """Get the use case for adding calibration tags."""
    return AddCalibrationTagUseCase(calibration_repository)


## ############################# ##
## DI WRAPPERS FOR TAGS
## ############################# ##


def get_tag_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
    # mongo_client: Annotated[AsyncIOMotorClient[Any], Depends(get_mongo_client)],
) -> TagRepository:
    """Provides a TagRepository instance based on REPOSITORY_TYPE env var."""
    repo_type = os.getenv("REPOSITORY_TYPE", "postgres").lower()
    if repo_type == "postgres":
        logger.info("Using PostgreSQL Tag Repository")
        return SqlAlchemyTagRepository(session)
    if repo_type == "mongo":
        logger.info("Using MongoDB Tag Repository")
        # return MongoTagRepository(mongo_client) # If/when implemented
        raise NotImplementedError("MongoTagRepository not implemented yet")
    if repo_type == "mock":
        logger.info("Using Mock Tag Repository")
        return MockTagRepository()
    logger.error(f"Invalid REPOSITORY_TYPE for Tag: {repo_type}")
    raise ValueError(f"Invalid REPOSITORY_TYPE: {repo_type}")


def get_create_tag_use_case(
    tag_repository: Annotated[TagRepository, Depends(get_tag_repository)],
) -> CreateTagUseCase:
    """Provides the CreateTagUseCase."""
    return CreateTagUseCase(tag_repository)


def get_list_tags_use_case(
    tag_repository: Annotated[TagRepository, Depends(get_tag_repository)],
) -> ListTagsUseCase:
    """Provides the ListTagsUseCase."""
    return ListTagsUseCase(tag_repository)


def get_add_tag_to_calibration_use_case(
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
    tag_repository: Annotated[TagRepository, Depends(get_tag_repository)],
) -> AddTagToCalibrationUseCase:
    """Provides the AddTagToCalibrationUseCase."""
    return AddTagToCalibrationUseCase(calibration_repository, tag_repository)


def get_remove_tag_from_calibration_use_case(
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
    tag_repository: Annotated[
        TagRepository, Depends(get_tag_repository)
    ],  # Tag repo needed for validation
) -> RemoveTagFromCalibrationUseCase:
    """Provides the RemoveTagFromCalibrationUseCase."""
    return RemoveTagFromCalibrationUseCase(calibration_repository, tag_repository)


def get_add_bulk_tags_to_calibration_use_case(
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
    tag_repository: Annotated[TagRepository, Depends(get_tag_repository)],
) -> AddBulkTagsToCalibrationUseCase:
    """Provides the AddBulkTagsToCalibrationUseCase."""
    return AddBulkTagsToCalibrationUseCase(calibration_repository, tag_repository)


def get_get_calibrations_by_tag_use_case(
    tag_repository: Annotated[TagRepository, Depends(get_tag_repository)],
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
) -> GetCalibrationsByTagUseCase:
    """Provides the GetCalibrationsByTagUseCase."""
    return GetCalibrationsByTagUseCase(tag_repository, calibration_repository)


def get_get_tags_for_calibration_use_case(
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
    tag_repository: Annotated[TagRepository, Depends(get_tag_repository)],
) -> GetTagsForCalibrationUseCase:
    """Provides the GetTagsForCalibrationUseCase."""
    return GetTagsForCalibrationUseCase(calibration_repository, tag_repository)


## ############################# ##
## USE CASES
## ############################# ##


# Add provider for ListCalibrationsUseCase
def get_list_calibrations_use_case(
    calibration_repository: Annotated[
        CalibrationRepository, Depends(get_calibration_repository)
    ],
) -> ListCalibrationsUseCase:
    """Provides the ListCalibrationsUseCase."""
    return ListCalibrationsUseCase(calibration_repository)


## ############################# ##
## CONTROLLERS
## ############################# ##


def get_add_calibration_controller(
    add_calibration_use_case: Annotated[
        AddCalibrationUseCase, Depends(get_add_calibration_use_case)
    ],
) -> AddCalibrationController:
    """Provides the AddCalibrationController."""
    return AddCalibrationController(add_calibration_use_case)


def get_list_calibrations_controller(
    list_calibrations_use_case: Annotated[
        ListCalibrationsUseCase, Depends(get_list_calibrations_use_case)
    ],
) -> ListCalibrationsController:
    """Provides the ListCalibrationsController."""
    return ListCalibrationsController(list_calibrations_use_case)


def get_get_tags_for_calibration_controller(
    get_tags_use_case: Annotated[
        GetTagsForCalibrationUseCase, Depends(get_get_tags_for_calibration_use_case)
    ],
) -> GetTagsForCalibrationController:
    """Provides the GetTagsForCalibrationController."""
    return GetTagsForCalibrationController(get_tags_use_case)


def get_create_tag_controller(
    create_tag_use_case: Annotated[CreateTagUseCase, Depends(get_create_tag_use_case)],
) -> CreateTagController:
    """Provides the CreateTagController."""
    return CreateTagController(create_tag_use_case)


def get_list_tags_controller(
    list_tags_use_case: Annotated[ListTagsUseCase, Depends(get_list_tags_use_case)],
) -> ListTagsController:
    """Provides the ListTagsController."""
    return ListTagsController(list_tags_use_case)


def get_add_tag_to_calibration_controller(
    add_tag_use_case: Annotated[
        AddTagToCalibrationUseCase, Depends(get_add_tag_to_calibration_use_case)
    ],
    create_tag_use_case: Annotated[  # Also depends on create tag UC
        CreateTagUseCase, Depends(get_create_tag_use_case)
    ],
    tag_repository: Annotated[  # And the repo directly
        TagRepository, Depends(get_tag_repository)
    ],
) -> AddTagToCalibrationController:
    """Provides the AddTagToCalibrationController."""
    return AddTagToCalibrationController(
        add_tag_use_case,
        create_tag_use_case,
        tag_repository,
    )


def get_remove_tag_from_calibration_controller(
    remove_tag_use_case: Annotated[
        RemoveTagFromCalibrationUseCase,
        Depends(get_remove_tag_from_calibration_use_case),
    ],
    tag_repository: Annotated[
        TagRepository, Depends(get_tag_repository)
    ],  # Also depends on tag repo
) -> RemoveTagFromCalibrationController:
    """Provides the RemoveTagFromCalibrationController."""
    return RemoveTagFromCalibrationController(remove_tag_use_case, tag_repository)


# def get_add_bulk_tags_to_calibration_controller(
#     add_bulk_tags_use_case: Annotated[
#         AddBulkTagsToCalibrationUseCase,
#         Depends(get_add_bulk_tags_to_calibration_use_case),
#     ],
#     tag_repository: Annotated[TagRepository, Depends(get_tag_repository)],
# ) -> AddBulkTagsToCalibrationController:
#     """Provides the AddBulkTagsToCalibrationController."""
#     # Ensure both arguments are passed here
#     return AddBulkTagsToCalibrationController(add_bulk_tags_use_case)


def get_get_calibrations_by_tag_controller(
    get_calibrations_by_tag_use_case: Annotated[
        GetCalibrationsByTagUseCase,
        Depends(get_get_calibrations_by_tag_use_case),
    ],
) -> GetCalibrationsByTagController:
    """Provides the GetCalibrationsByTagController."""
    return GetCalibrationsByTagController(get_calibrations_by_tag_use_case)
