# tests/unit/interface_adapters/controllers/tags/test_add_bulk_tags_to_calibration_controller.py
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
    TagNotFoundError,
    UseCaseError,
    ValidationError,
)
from src.application.use_cases.tags.add_bulk_tags_to_calibration import (
    AddBulkTagsToCalibrationInput,
    AddBulkTagsToCalibrationOutput,
    AddBulkTagsToCalibrationUseCase,
)
from src.drivers.rest.schemas.tag_schemas import (
    AssociationResponse,
    BulkAddTagsRequest,
    BulkAddTagsResponse,
)
from src.entities.exceptions import (
    DatabaseOperationError,
    InputParseError,
    NotFoundError,
)
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.interface_adapters.controllers.tags.add_bulk_tags_to_calibration_controller import (
    AddBulkTagsToCalibrationController,
)
from src.interface_adapters.presenters.tag_presenter import TagPresenter


@pytest.fixture
def mock_add_bulk_tags_use_case() -> AsyncMock:
    return AsyncMock(spec=AddBulkTagsToCalibrationUseCase)


@pytest.fixture
def add_bulk_tags_controller(
    mock_add_bulk_tags_use_case: AsyncMock,
) -> AddBulkTagsToCalibrationController:
    return AddBulkTagsToCalibrationController(
        add_bulk_tags_use_case=mock_add_bulk_tags_use_case
    )


@pytest.fixture
def sample_calibration_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_tag_ids() -> list[UUID]:
    return [uuid4() for _ in range(3)]


@pytest.fixture
def valid_request(sample_tag_ids: list[UUID]) -> BulkAddTagsRequest:
    return BulkAddTagsRequest(tag_ids=sample_tag_ids)


@pytest.fixture
def sample_associations(
    sample_calibration_id: UUID, sample_tag_ids: list[UUID]
) -> list[CalibrationTagAssociation]:
    return [
        CalibrationTagAssociation(calibration_id=sample_calibration_id, tag_id=tag_id)
        for tag_id in sample_tag_ids
    ]


@pytest.fixture
def expected_success_response(
    sample_associations: list[CalibrationTagAssociation],
) -> BulkAddTagsResponse:
    # Construct AssociationResponse objects (data can be dummy for mocked presenter)
    added_assocs_response = [
        AssociationResponse(
            id=assoc.id,
            calibration_id=assoc.calibration_id,
            tag_id=assoc.tag_id,
            created_at=assoc.created_at,  # Assuming assoc has this
            archived_at=None,
        )
        for assoc in sample_associations
    ]
    return BulkAddTagsResponse(
        added_associations=added_assocs_response,
        skipped_tag_ids=[],  # Assuming none skipped in this success case
    )


# --- Test Cases ---


@pytest.mark.asyncio
async def test_add_bulk_tags_success(
    add_bulk_tags_controller: AddBulkTagsToCalibrationController,
    mock_add_bulk_tags_use_case: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: BulkAddTagsRequest,
    sample_associations: list[CalibrationTagAssociation],
    expected_success_response: BulkAddTagsResponse,
):
    """Test successful bulk adding of tags."""
    # Arrange
    mock_output = AddBulkTagsToCalibrationOutput(
        added_associations=sample_associations, skipped_tag_ids=[]
    )
    # Make the use case mock callable
    mock_add_bulk_tags_use_case.return_value = mock_output

    with patch.object(
        TagPresenter, "present_bulk_add_output", return_value=expected_success_response
    ) as mock_presenter:
        # Act
        response = await add_bulk_tags_controller.add_bulk_tags_to_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

        # Assert
        mock_add_bulk_tags_use_case.assert_awaited_once()
        # Check input DTO passed to the use case
        call_args = mock_add_bulk_tags_use_case.call_args[0][0]
        assert isinstance(call_args, AddBulkTagsToCalibrationInput)
        assert call_args.calibration_id == sample_calibration_id
        # Compare sets for unordered comparison
        assert set(call_args.tag_ids) == set(valid_request.tag_ids)

        mock_presenter.assert_called_once_with(mock_output)
        assert response == expected_success_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_type", "expected_exception"),
    [
        (ValidationError("Empty list provided"), InputParseError),
        (CalibrationNotFoundError("Cal not found"), NotFoundError),
        (TagNotFoundError("Tag XYZ not found"), NotFoundError),
        (DatabaseOperationError("DB connection error"), DatabaseOperationError),
        (UseCaseError("Internal logic failed"), UseCaseError),
        (Exception("Completely unexpected"), UseCaseError),
    ],
)
async def test_add_bulk_tags_exceptions(
    add_bulk_tags_controller: AddBulkTagsToCalibrationController,
    mock_add_bulk_tags_use_case: AsyncMock,
    sample_calibration_id: UUID,
    valid_request: BulkAddTagsRequest,  # Use valid request structure
    error_type: Exception,
    expected_exception: type[Exception],
):
    """Test controller exception handling during bulk tag adding."""
    # Arrange
    # Make the use case mock callable and raise the error
    mock_add_bulk_tags_use_case.side_effect = error_type

    # Act & Assert
    with pytest.raises(expected_exception):
        await add_bulk_tags_controller.add_bulk_tags_to_calibration(
            calibration_id=sample_calibration_id, request=valid_request
        )

    # Assert use case was called (as errors happen *during* its execution)
    mock_add_bulk_tags_use_case.assert_awaited_once()
    call_args = mock_add_bulk_tags_use_case.call_args[0][0]
    assert isinstance(call_args, AddBulkTagsToCalibrationInput)
    assert call_args.calibration_id == sample_calibration_id
    assert set(call_args.tag_ids) == set(valid_request.tag_ids)
