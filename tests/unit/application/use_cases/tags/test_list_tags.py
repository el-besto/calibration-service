from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.tags.list_tags import ListTagsOutput, ListTagsUseCase
from src.entities.exceptions import DatabaseOperationError
from tests.utils.entity_factories import create_tag


@pytest.fixture
def list_tags_use_case(mock_tag_repository: AsyncMock) -> ListTagsUseCase:
    """Fixture for the ListTagsUseCase with mocked repository."""
    return ListTagsUseCase(tag_repository=mock_tag_repository)


@pytest.mark.asyncio
async def test_list_tags_success_no_tags(
    list_tags_use_case: ListTagsUseCase, mock_tag_repository: AsyncMock
):
    """Test successfully listing tags when the repository returns an empty list."""
    # Arrange
    mock_tag_repository.list_all.return_value = []

    # Act
    # Use cases typically have an execute method
    output = await list_tags_use_case.execute()

    # Assert
    assert isinstance(output, ListTagsOutput)
    assert output.tags == []
    mock_tag_repository.list_all.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_list_tags_success_with_tags(
    list_tags_use_case: ListTagsUseCase, mock_tag_repository: AsyncMock
):
    """Test successfully listing tags when the repository returns multiple tags."""
    # Arrange
    # Use the factory to create Tag instances directly
    expected_tags = [
        create_tag(name="Tag 1"),
        create_tag(name="Tag 2"),
        create_tag(name="Tag 3"),
    ]
    mock_tag_repository.list_all.return_value = expected_tags

    # Act
    output = await list_tags_use_case.execute()  # Call execute method

    # Assert
    assert isinstance(output, ListTagsOutput)
    assert len(output.tags) == len(expected_tags)

    # Convert lists to dictionaries keyed by ID for easier comparison
    output_tags_dict = {tag.id: tag for tag in output.tags}
    expected_tags_dict = {tag.id: tag for tag in expected_tags}

    # Check if the sets of IDs are the same
    assert output_tags_dict.keys() == expected_tags_dict.keys()

    # Compare attributes of each tag
    for tag_id, output_tag in output_tags_dict.items():
        expected_tag = expected_tags_dict[tag_id]
        assert output_tag.name == expected_tag.name
        assert output_tag.created_at == expected_tag.created_at  # Compare datetimes

    mock_tag_repository.list_all.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_list_tags_repository_error(
    list_tags_use_case: ListTagsUseCase, mock_tag_repository: AsyncMock
):
    """Test error handling when the repository raises an exception."""
    # Arrange
    error_message = "Database connection failed"
    mock_tag_repository.list_all.side_effect = DatabaseOperationError(error_message)

    # Act & Assert
    with pytest.raises(DatabaseOperationError, match=error_message):
        await list_tags_use_case.execute()  # Call execute method

    mock_tag_repository.list_all.assert_awaited_once_with()
