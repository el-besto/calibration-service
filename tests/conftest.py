"""Common test fixtures for the application."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pytest_asyncio import is_async_test
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session

# Import from the consolidated config location
from src.config.logger import setup_test_logger
from src.drivers.rest.dependencies import get_mongo_client
from src.drivers.rest.main import app as fastapi_app


# Add command line option for --log-debug (renamed from --debug)
def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--log-debug",  # Renamed option
        action="store_true",
        default=False,
        help="Enable debug logging level for tests via test logger setup",
    )


# Add conditional logging setup fixture
@pytest.fixture(autouse=True)
def setup_logging(request: pytest.FixtureRequest) -> None:
    """Set up logging using the test config if --log-debug is passed."""
    if request.config.getoption("--log-debug"):  # Check renamed option
        setup_test_logger()


@pytest.fixture
def app() -> FastAPI:
    """Get the FastAPI application instance."""
    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Get a test client for testing the API."""
    with TestClient(
        app=app,
        base_url="http://test",
        raise_server_exceptions=True,
        follow_redirects=True,
    ) as client:
        logger.debug("Starting test client")
        yield client
        logger.debug("Closing test client")


def pytest_collection_modifyitems(items: Any) -> None:
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture
def client_mongo(app: FastAPI) -> Generator[AsyncIOMotorClient[Any], None, None]:
    """Get a mock MongoDB client for testing."""
    # Create a mock MongoDB client
    mock_client = MagicMock(spec=AsyncIOMotorClient)

    # Mock the database and collection
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.drop = AsyncMock()

    # Set up the mock collection chain
    mock_db = MagicMock()
    mock_db.calibration = mock_collection
    mock_client.calibrations = mock_db

    # Override the dependency
    app.dependency_overrides[get_mongo_client] = lambda: mock_client

    yield mock_client

    # Clean up
    del app.dependency_overrides[get_mongo_client]


@pytest.fixture
def client_postgres(app: FastAPI) -> Generator[AsyncSession, None, None]:
    """Get a mock PostgreSQL client for testing."""
    # Create a mock SQLAlchemy session
    mock_session = MagicMock(spec=AsyncSession)

    # Mock the execute result chain
    mock_scalar_result = MagicMock()
    mock_scalar_result.first.return_value = None

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalar_result

    # Make execute return the mock result immediately
    mock_session.execute = AsyncMock(return_value=mock_execute_result)
    mock_session.add = MagicMock()
    mock_session.add_all = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.rollback = AsyncMock()

    # Mock sync_session for internal SQLAlchemy operations
    mock_session.sync_session = MagicMock()
    mock_session.sync_session.execute = MagicMock()

    # Override the dependency
    app.dependency_overrides[get_session] = lambda: mock_session

    yield mock_session

    # Clean up
    del app.dependency_overrides[get_session]
