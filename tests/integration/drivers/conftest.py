from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session
from src.drivers.rest.main import app


@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def mock_session() -> AsyncGenerator[AsyncSession, None]:
    """Mock SQLAlchemy session for testing FastAPI endpoints."""
    session = MagicMock(spec=AsyncSession)

    # Mock the execute result chain
    mock_scalar_result = MagicMock()
    mock_scalar_result.first.return_value = None

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalar_result

    # Make execute return the mock result immediately
    session.execute = AsyncMock(return_value=mock_execute_result)
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    session.rollback = AsyncMock()

    # Mock sync_session for internal SQLAlchemy operations
    session.sync_session = MagicMock()
    session.sync_session.execute = MagicMock()

    app.dependency_overrides[get_session] = lambda: session
    yield session
    del app.dependency_overrides[get_session]
