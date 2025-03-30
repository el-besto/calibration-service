"""Common test fixtures for the application."""

import asyncio
from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger

from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
        logger.info("Starting test client")
        yield client
        logger.info("Closing test client")
