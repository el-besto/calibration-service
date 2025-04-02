from dataclasses import dataclass
from datetime import UTC, datetime

from src.entities.exceptions import InputParseError


@dataclass(frozen=True)
class Iso8601Timestamp:
    """
    A value object representing an ISO 8601 timestamp.

    This class encapsulates a string value that should conform to the ISO 8601
    timestamp standard. It provides functionalities to validate the timestamp,
    convert it to a `datetime` object, and get its string representation.

    :ivar value: The ISO 8601 timestamp string encapsulated by the object.
    :type value: str
    """

    value: str

    def __post_init__(self):
        # Validate that the given `value` is a proper ISO 8601 timestamp.
        if not self._is_valid_iso8601(self.value):
            # Using InputParseError to capture the validation failure
            raise InputParseError(
                message=f"Invalid ISO 8601 timestamp: {self.value}",
            ) from ValueError(f"Provided value is not valid ISO 8601: {self.value}")

    @staticmethod
    def _is_valid_iso8601(timestamp: str) -> bool:
        """Validate if the input string is a valid ISO 8601 timestamp."""
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            return False
        else:
            return True

    def to_datetime(self) -> datetime:
        """Convert the ISO 8601 timestamp to a Python `datetime` object."""
        return datetime.fromisoformat(self.value)

    @staticmethod
    def now() -> datetime:
        """Provide ISO 8601 timestamp of UTC now."""
        return datetime.now(UTC)

    def __str__(self) -> str:
        """Get the string representation of the timestamp."""
        return self.value

    @classmethod
    def is_valid(cls, timestamp: str) -> bool:
        """Check if the timestamp is valid ISO 8601 format."""
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def validate(timestamp: str) -> bool:
        """Validate that the timestamp is in ISO 8601 format."""
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            return False
        else:
            return True
