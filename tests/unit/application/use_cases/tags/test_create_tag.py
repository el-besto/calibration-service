from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.use_cases.tags.create_tag import (
    CreateTagInput,
    CreateTagOutput,
    CreateTagUseCase,
)
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.tag import Tag
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp


@pytest.fixture
def create_tag_use_case(mock_tag_repository: AsyncMock) -> CreateTagUseCase:
    """Fixture for the CreateTagUseCase with mocked repository."""
    return CreateTagUseCase(tag_repository=mock_tag_repository)


@pytest.mark.asyncio
async def test_create_tag_success(
    create_tag_use_case: CreateTagUseCase, mock_tag_repository: AsyncMock
):
    """Test successful creation of a tag."""
    # Arrange
    mock_tag_repository.get_by_name.return_value = None
    input_data = CreateTagInput(name="New Tag")
    # We don't need expected_tag factory here, the mock handles the return value simulation

    # Configure mock to return a tag instance when add is called
    # The use case should generate the ID and timestamp
    async def side_effect(tag: Tag):
        # Simulate the repository adding the tag and returning it (often with generated ID/timestamps)
        # Ensure the passed tag has the correct name
        assert tag.name == input_data.name
        # Return a tag object similar to what the real repo would return
        return Tag(
            id=UUID(
                "123e4567-e89b-12d3-a456-426614174000"
            ),  # Use a fixed UUID for predictability in mock
            name=tag.name,
            created_at=Iso8601Timestamp(
                "2023-01-01T12:00:00Z"
            ).to_datetime(),  # Convert to datetime
        )

    mock_tag_repository.add.side_effect = side_effect

    # Act
    output = await create_tag_use_case.execute(input_data)

    # Assert
    assert isinstance(output, CreateTagOutput)
    mock_tag_repository.add.assert_awaited_once()

    # Check the tag passed to the repository's add method
    call_args = mock_tag_repository.add.call_args[0][0]
    assert isinstance(call_args, Tag)
    assert call_args.name == input_data.name
    # The ID and created_at are generated within the use case before passing to repo,
    # so we check their types on the passed object
    assert isinstance(call_args.id, UUID)
    assert isinstance(call_args.created_at, datetime)

    # Check the output contains a tag with the correct name and expected types for generated fields
    assert output.tag.name == input_data.name
    assert isinstance(output.tag.id, UUID)
    assert isinstance(output.tag.created_at, datetime)


@pytest.mark.asyncio
async def test_create_tag_error(
    create_tag_use_case: CreateTagUseCase, mock_tag_repository: AsyncMock
):
    """Test error handling during tag creation (e.g., database error)."""
    # Arrange
    mock_tag_repository.get_by_name.return_value = None
    input_data = CreateTagInput(name="Error Tag")
    error_message = "Failed to save tag"
    # Simulate a database error during the add operation
    mock_tag_repository.add.side_effect = DatabaseOperationError(error_message)

    # Act & Assert
    with pytest.raises(DatabaseOperationError, match=error_message):
        await create_tag_use_case.execute(input_data)

    # Verify that the repository's add method was called
    mock_tag_repository.add.assert_awaited_once()
    call_args = mock_tag_repository.add.call_args[0][0]
    assert isinstance(call_args, Tag)
    assert call_args.name == input_data.name
