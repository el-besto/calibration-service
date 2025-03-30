from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.use_cases.exceptions import UseCaseError, ValidationError
from src.application.use_cases.tags.create_tag import (
    CreateTagInput,
    CreateTagOutput,
    CreateTagUseCase,
)
from src.drivers.rest.schemas.tag_schemas import TagCreateRequest, TagResponse
from src.entities.exceptions import DatabaseOperationError, InputParseError
from src.entities.models.tag import Tag
from src.interface_adapters.controllers.tags.create_tag_controller import (
    CreateTagController,
)
from tests.utils.entity_factories import create_tag  # Import factory


@pytest.fixture
def mock_create_tag_use_case() -> AsyncMock:
    return AsyncMock(spec=CreateTagUseCase)


@pytest.fixture
def create_tag_controller(mock_create_tag_use_case: AsyncMock) -> CreateTagController:
    return CreateTagController(create_tag_use_case=mock_create_tag_use_case)


@pytest.fixture
def valid_request() -> TagCreateRequest:
    return TagCreateRequest(name="new_tag_name")


@pytest.fixture
def sample_tag(valid_request: TagCreateRequest) -> Tag:
    # Use factory, overriding the name from valid_request
    # Let factory handle the ID unless specific ID is needed for a test
    return create_tag(name=valid_request.name)


@pytest.mark.asyncio
@patch(
    "src.interface_adapters.controllers.tags.create_tag_controller.TagPresenter.present_tag"
)
async def test_create_tag_success(
    mock_present_tag: MagicMock,
    create_tag_controller: CreateTagController,
    mock_create_tag_use_case: AsyncMock,
    valid_request: TagCreateRequest,
    sample_tag: Tag,
):
    """Test successful tag creation."""
    # Arrange
    mock_output = CreateTagOutput(tag=sample_tag)
    mock_create_tag_use_case.execute.return_value = mock_output

    expected_response = TagResponse(id=sample_tag.id, name=sample_tag.name)
    mock_present_tag.return_value = expected_response

    # Act
    response = await create_tag_controller.create_tag(valid_request)

    # Assert
    mock_create_tag_use_case.execute.assert_awaited_once()
    call_args = mock_create_tag_use_case.execute.call_args[0][0]
    assert isinstance(call_args, CreateTagInput)
    assert call_args.name == valid_request.name

    mock_present_tag.assert_called_once_with(sample_tag)
    assert response == expected_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_type", "expected_exception"),
    [
        (
            ValidationError("Tag name too short"),
            InputParseError,
        ),  # Maps to InputParseError
        (DatabaseOperationError("Duplicate name"), DatabaseOperationError),
        (UseCaseError("Some internal logic failed"), UseCaseError),
        (Exception("Completely unexpected"), UseCaseError),  # Test base Exception catch
    ],
)
async def test_create_tag_exceptions(
    create_tag_controller: CreateTagController,
    mock_create_tag_use_case: AsyncMock,
    valid_request: TagCreateRequest,
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test controller exception handling during tag creation."""
    # Arrange
    mock_create_tag_use_case.execute.side_effect = error_type

    # Act & Assert
    with pytest.raises(expected_exception):
        await create_tag_controller.create_tag(valid_request)

    mock_create_tag_use_case.execute.assert_awaited_once()
    call_args = mock_create_tag_use_case.execute.call_args[0][0]
    assert isinstance(call_args, CreateTagInput)
    assert call_args.name == valid_request.name
