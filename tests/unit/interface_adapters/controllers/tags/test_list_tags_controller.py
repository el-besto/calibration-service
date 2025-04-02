from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from src.application.use_cases.exceptions import UseCaseError
from src.application.use_cases.tags.list_tags import (
    ListTagsOutput,
    ListTagsUseCase,
)
from src.drivers.rest.schemas.tag_schemas import TagListResponse, TagResponse
from src.entities.exceptions import DatabaseOperationError
from src.entities.models.tag import Tag
from src.interface_adapters.controllers.tags.list_tags_controller import (
    ListTagsController,
)
from tests.utils.entity_factories import create_tag


@pytest.fixture
def mock_list_tags_use_case() -> AsyncMock:
    return AsyncMock(spec=ListTagsUseCase)


@pytest.fixture
def list_tags_controller(mock_list_tags_use_case: AsyncMock) -> ListTagsController:
    return ListTagsController(list_tags_use_case=mock_list_tags_use_case)


@pytest.fixture
def sample_tag_list() -> list[Tag]:
    return [
        create_tag(name="tag1", tag_id=UUID("33333333-3333-3333-3333-333333333331")),
        create_tag(name="tag2", tag_id=UUID("33333333-3333-3333-3333-333333333332")),
        create_tag(
            name="beta_tag", tag_id=UUID("33333333-3333-3333-3333-333333333333")
        ),
    ]


@pytest.mark.asyncio
@patch(
    "src.interface_adapters.controllers.tags.list_tags_controller.TagPresenter.present_tag_list"
)
async def test_list_tags_success(
    mock_present_list: MagicMock,
    list_tags_controller: ListTagsController,
    mock_list_tags_use_case: AsyncMock,
    sample_tag_list: list[Tag],
):
    """Test successful listing of all tags."""
    # Arrange
    mock_output = ListTagsOutput(tags=sample_tag_list)
    mock_list_tags_use_case.execute.return_value = mock_output

    expected_response = TagListResponse(
        # Use factory or direct instantiation if needed, or rely on mock return value
        tags=[TagResponse(id=tag.id, name=tag.name) for tag in sample_tag_list]
    )
    mock_present_list.return_value = expected_response

    # Act
    response = await list_tags_controller.list_all_tags()

    # Assert
    mock_list_tags_use_case.execute.assert_awaited_once()
    mock_present_list.assert_called_once_with(sample_tag_list)
    assert response == expected_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_type", "expected_exception"),
    [
        (DatabaseOperationError("DB connection failed"), DatabaseOperationError),
        (UseCaseError("Internal logic error"), UseCaseError),
        (Exception("Completely unexpected"), UseCaseError),  # Test base Exception catch
    ],
)
async def test_list_tags_exceptions(
    list_tags_controller: ListTagsController,
    mock_list_tags_use_case: AsyncMock,
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test controller exception handling during tag listing."""
    # Arrange
    mock_list_tags_use_case.execute.side_effect = error_type

    # Act & Assert
    with pytest.raises(expected_exception):
        await list_tags_controller.list_all_tags()

    mock_list_tags_use_case.execute.assert_awaited_once()
