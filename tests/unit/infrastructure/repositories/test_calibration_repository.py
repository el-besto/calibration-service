import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.models.calibration import Calibration, Measurement
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.infrastructure.orm_models import (
    CalibrationORM,
    CalibrationTagAssociationORM,
)
from src.infrastructure.repositories.calibration_repository.postgres_repository import (
    SqlAlchemyCalibrationRepository,
)
from tests.utils.entity_factories import create_calibration_tag_association, create_tag

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session() -> MagicMock:
    """Fixture to create a mock AsyncSession."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session: MagicMock) -> SqlAlchemyCalibrationRepository:
    """Fixture to create a repository instance with a mock session."""
    return SqlAlchemyCalibrationRepository(session=mock_session)


@pytest.fixture
def sample_calibration_entity() -> Calibration:
    """Fixture for a sample Calibration entity."""
    now = datetime.now(UTC)
    cal_id = uuid.uuid4()
    tag1 = create_tag(tag_id=uuid.uuid4(), name="tag1")
    tag2 = create_tag(tag_id=uuid.uuid4(), name="tag2")
    # Calibration entity expects a list of associated Tag entities
    return Calibration(
        id=cal_id,
        measurement=Measurement(value=10.5, type=CalibrationType.temp),
        timestamp=Iso8601Timestamp(now.isoformat()),
        username="testuser",
        tags=[tag1, tag2],  # Use Tag entities
    )


@pytest.fixture
def sample_calibration_orm(sample_calibration_entity: Calibration) -> CalibrationORM:
    """Fixture for a sample CalibrationORM object based on the entity."""
    # Directly use the from_entity method for consistency
    return CalibrationORM.from_entity(sample_calibration_entity)


async def test_get_calibration_found(
    repository: SqlAlchemyCalibrationRepository,
    mock_session: MagicMock,
    sample_calibration_orm: CalibrationORM,
):
    """Test getting a calibration by ID when it exists."""
    calibration_id = sample_calibration_orm.id

    # Mock the final scalar object's .first() method
    mock_scalar_result = MagicMock()
    mock_scalar_result.first.return_value = sample_calibration_orm

    # Mock the object returned by .scalars()
    mock_scalars_obj = MagicMock()
    mock_scalars_obj.scalars.return_value = mock_scalar_result

    # Configure the session's execute AsyncMock to return the scalars object when awaited
    mock_session.execute = AsyncMock(return_value=mock_scalars_obj)

    # Call the get method
    result = await repository.get(id=calibration_id)

    # Assertions
    mock_session.execute.assert_awaited_once()  # Check it was awaited
    assert result is not None
    assert result.id == calibration_id
    assert result.measurement == sample_calibration_orm.to_entity().measurement
    assert len(result.tags) == len(sample_calibration_orm.tag_associations)


async def test_get_calibration_not_found(
    repository: SqlAlchemyCalibrationRepository,
    mock_session: MagicMock,
):
    """Test getting a calibration by ID when it does not exist."""
    calibration_id = uuid.uuid4()

    # Mock the final scalar object's .first() method to return None
    mock_scalar_result = MagicMock()
    mock_scalar_result.first.return_value = None

    # Mock the object returned by .scalars()
    mock_scalars_obj = MagicMock()
    mock_scalars_obj.scalars.return_value = mock_scalar_result

    # Configure the session's execute AsyncMock
    mock_session.execute = AsyncMock(return_value=mock_scalars_obj)

    # Call the get method
    result = await repository.get(id=calibration_id)

    # Assertions
    mock_session.execute.assert_awaited_once()  # Check it was awaited
    assert result is None


@pytest.mark.asyncio
async def test_add_calibration(
    repository: SqlAlchemyCalibrationRepository,
    mock_session: MagicMock,
    sample_calibration_entity: Calibration,
):
    """Test adding a new calibration."""
    # Call the add_calibration method
    with patch(
        "src.infrastructure.orm_models.CalibrationORM.from_entity",
    ) as mock_from_entity:
        mock_orm = MagicMock(spec=CalibrationORM)
        # Ensure the mock ORM has a 'tags' attribute for the refresh call
        mock_orm.tags = []  # Or mock the actual ORM tags if needed for assertion
        mock_orm.to_entity.return_value = sample_calibration_entity
        mock_from_entity.return_value = mock_orm

        result = await repository.add_calibration(sample_calibration_entity)

        # Assertions
        mock_from_entity.assert_called_once_with(sample_calibration_entity)
        mock_session.add.assert_called_once_with(mock_orm)
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

        assert result is not None
        assert result.id == sample_calibration_entity.id
        assert result.username == sample_calibration_entity.username
        assert len(result.tags) == len(sample_calibration_entity.tags)


@pytest.mark.asyncio
async def test_add_tags_to_calibration(
    repository: SqlAlchemyCalibrationRepository,
    mock_session: MagicMock,
):
    """Test adding tags to an existing calibration."""
    calibration_id = uuid.uuid4()
    # The add_tags method expects CalibrationTagAssociation entities
    tag1_id = uuid.uuid4()
    tag2_id = uuid.uuid4()
    associations_to_add = [
        create_calibration_tag_association(
            calibration_id=calibration_id,
            tag_id=tag1_id,
        ),
        create_calibration_tag_association(
            calibration_id=calibration_id,
            tag_id=tag2_id,
        ),
    ]

    # Call the add_tags method
    success = await repository.add_tags(calibration_id, associations_to_add)

    # Assertions
    assert success is True
    assert mock_session.add_all.call_count == 1
    args, _ = mock_session.add_all.call_args
    added_orms = args[0]
    assert len(added_orms) == len(associations_to_add)
    assert all(isinstance(orm, CalibrationTagAssociationORM) for orm in added_orms)
    # Check that the ORM objects have the correct IDs
    assert {orm.calibration_id for orm in added_orms} == {calibration_id}
    assert {orm.tag_id for orm in added_orms} == {tag1_id, tag2_id}

    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()


async def test_add_tags_no_tags(
    repository: SqlAlchemyCalibrationRepository,
    mock_session: MagicMock,
):
    """Test adding tags when the list is empty or None."""
    calibration_id = uuid.uuid4()

    success_none = await repository.add_tags(calibration_id, None)
    success_empty = await repository.add_tags(calibration_id, [])

    assert success_none is True
    assert success_empty is True
    mock_session.add_all.assert_not_called()
    mock_session.commit.assert_not_called()
