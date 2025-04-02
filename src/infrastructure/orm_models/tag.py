import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import UUID as UUID_SQL, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Entities
from src.entities.models.calibration_tag_association import CalibrationTagAssociation
from src.entities.models.tag import Tag
from src.infrastructure.orm_models.base import Base
from src.infrastructure.orm_models.calibration import CalibrationORM


class CalibrationTagAssociationORM(Base):
    __tablename__ = "calibration_tag_associations"

    id: Mapped[UUID] = mapped_column(UUID_SQL, primary_key=True, default=uuid.uuid4)
    calibration_id: Mapped[UUID] = mapped_column(
        UUID_SQL, ForeignKey("calibrations.id", ondelete="CASCADE"), index=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        UUID_SQL, ForeignKey("tags.id", ondelete="CASCADE"), index=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,  # Ensure nullable is set
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    calibration: Mapped[CalibrationORM] = relationship(
        back_populates="tag_associations"
    )
    tag: Mapped["TagORM"] = relationship(back_populates="calibration_associations")

    def to_entity(self) -> CalibrationTagAssociation:
        return CalibrationTagAssociation(
            id=self.id,
            archived_at=self.archived_at,
            tag_id=self.tag_id,
            calibration_id=self.calibration_id,
            created_at=self.created_at,
        )

    # from_entity might not be needed if repo manages creation directly
    @staticmethod
    def from_entity(
        entity: CalibrationTagAssociation,
    ) -> "CalibrationTagAssociationORM":
        return CalibrationTagAssociationORM(
            id=entity.id,
            calibration_id=entity.calibration_id,
            tag_id=entity.tag_id,
            archived_at=entity.archived_at,
            created_at=entity.created_at,
        )


class TagORM(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(UUID_SQL, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationship to the association object
    calibration_associations: Mapped[list["CalibrationTagAssociationORM"]] = (
        relationship(
            "CalibrationTagAssociationORM",
            back_populates="tag",
            cascade="all, delete-orphan",
        )
    )

    # REMOVED conflicting secondary relationship
    # calibrations: Mapped[list["CalibrationORM"]] = relationship(...)

    def to_entity(self) -> Tag:
        return Tag(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
        )

    # from_entity might not be needed if repo manages creation directly
    @staticmethod
    def from_entity(entity: Tag) -> "TagORM":
        return TagORM(
            id=entity.id,
            name=entity.name,
            created_at=entity.created_at,
        )
