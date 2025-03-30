# from ulid import ULID
from uuid import UUID


class UseCaseError(Exception):
    """Base class for exceptions raised by use cases."""


class CalibrationNotFoundError(UseCaseError):
    """Raised when a specific calibration is not found."""


class TagNotFoundError(UseCaseError):
    """Raised when a specific tag is not found."""


class AssociationNotFoundError(UseCaseError):
    """Raised when a specific calibration-tag association is not found."""


class ValidationError(UseCaseError):
    """Raised when input validation fails."""


class CalibrationConflictError(Exception):
    def __init__(self, calibration_id: UUID):
        self.id = calibration_id

    def __str__(self) -> str:
        return f"Calibration conflict found: {self.id}"


# Add more specific use case exceptions as needed
