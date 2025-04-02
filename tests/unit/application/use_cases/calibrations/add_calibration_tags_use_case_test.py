"""Test the add calibration tags use case."""

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from src.application.repositories.calibration_repository import CalibrationRepository
from src.application.use_cases.calibrations.add_calibration_tags import (
    AddCalibrationTagUseCase,
)
from src.entities.models.calibration import Measurement
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.value_objects.calibration_type import CalibrationType
from src.infrastructure.repositories.calibration_repository.in_memory_repository import (
    InMemoryCalibrationRepository,
)
from tests.utils.entity_factories import create_calibration  # Updated import

if TYPE_CHECKING:
    from src.entities.models.calibration import Calibration


@pytest.fixture
def calibration_repository() -> CalibrationRepository:
    """Create a mock calibration repository."""
    repo = InMemoryCalibrationRepository()
    repo.clear()
    return repo


@pytest.fixture
def add_calibration_tags_use_case(
    calibration_repository: CalibrationRepository,
) -> AddCalibrationTagUseCase:
    """Create an add calibration tags use case with the mock repository."""
    return AddCalibrationTagUseCase(calibration_repository)


@pytest.mark.asyncio
@pytest.mark.parametrize("num_associations", [1, 2, 3])
async def test_calibration_tags_successfully_added(
    calibration_repository: InMemoryCalibrationRepository,
    add_calibration_tags_use_case: AddCalibrationTagUseCase,
    num_associations: int,
):
    """Test that calibration tag associations are successfully added via the use case."""

    # ARRANGE
    calibration_id = uuid4()
    calibration = create_calibration(
        calibration_id=calibration_id,
        measurement=Measurement(value=1.0, type=CalibrationType.gain),
        tags=[],  # Calibration initially has no tags
        username="user_add_tags",
    )
    # Add the initial calibration directly to the mock repo for the test setup
    await calibration_repository.add_calibration(calibration)

    # Create test associations
    test_associations = [
        CalibrationTagAssociation(
            tag_id=uuid4(),  # Assume these tags exist elsewhere
            calibration_id=calibration_id,
            # id, created_at, archived_at handled by entity defaults
        )
        for _ in range(num_associations)
    ]

    # ACT
    result: Calibration | None = await add_calibration_tags_use_case(
        calibration_id,
        test_associations,
    )

    # ASSERT
    assert result is not None
    assert result.id == calibration_id

    # Verify associations were added using the dedicated repo method
    added_associations = (
        await calibration_repository.get_tag_associations_for_calibration(
            calibration_id
        )
    )
    assert len(added_associations) == num_associations
