from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP, UUID as SQLUUID, Enum as SQLEnum, Float, String

from src.entities.models.calibration import Calibration, Measurement
from src.entities.value_objects.calibration_type import CalibrationType
from src.entities.value_objects.iso_8601_timestamp import Iso8601Timestamp
from src.infrastructure.orm_models.base import Base

if TYPE_CHECKING:
    from src.infrastructure.orm_models.tag import CalibrationTagAssociationORM


class CalibrationORM(Base):
    __tablename__ = "calibrations"

    id: Mapped[UUID] = mapped_column(SQLUUID(as_uuid=True), primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    type: Mapped[CalibrationType] = mapped_column(SQLEnum(CalibrationType))
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    username: Mapped[str] = mapped_column(String)

    # Keep ONLY the relationship to the association objects
    tag_associations: Mapped[list["CalibrationTagAssociationORM"]] = relationship(
        "CalibrationTagAssociationORM",
        back_populates="calibration",  # Link back to the association's .calibration attr
        cascade="all, delete-orphan",  # Cascade operations
        lazy="selectin",  # Keep lazy strategy if desired
    )

    def to_entity(self) -> Calibration:
        # When converting to entity, map associated Tags via the association objects
        entity_tags = [
            assoc.tag.to_entity()
            for assoc in self.tag_associations
            if assoc.tag and assoc.archived_at is None
        ]
        return Calibration(
            id=self.id,
            measurement=Measurement(value=self.value, type=self.type),
            timestamp=Iso8601Timestamp(self.timestamp.isoformat()),
            username=self.username,
            tags=entity_tags,  # Use the constructed list of Tag entities
        )

    @classmethod
    def from_entity(cls, entity: Calibration) -> "CalibrationORM":
        return cls(
            id=entity.id,
            value=entity.measurement.value,
            type=entity.measurement.type,
            timestamp=entity.timestamp.to_datetime(),
            username=entity.username,
            tag_associations=[],  # Initialize as empty
        )
