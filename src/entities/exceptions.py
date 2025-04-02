from uuid import UUID


class ExternalError(Exception):
    """Base class for external service errors.

    This class is used to wrap exceptions from external services and provide
    additional context about the error.

    It utilizes Python's built-in exception chaining (__cause__).
    """

    def __init__(self, message: str) -> None:
        """Initialize the external error.

        Args:
            message: The error message.
        """
        super().__init__(message)

    def __str__(self) -> str:
        """Get the string representation of the error.

        Includes the cause automatically if `raise ... from e` was used.
        """
        return super().__str__()


class DatabaseOperationError(ExternalError):
    """Error raised when a database operation fails.

    This error is used to wrap database-specific exceptions and provide
    a consistent interface for handling database errors.
    """


class NotFoundError(ExternalError):
    """Error raised when a requested resource is not found.

    This error indicates that the requested resource does not exist
    in the system.
    """


class InputParseError(ExternalError):
    """Error raised when input data cannot be parsed.

    This error indicates that the provided input data is invalid
    or cannot be parsed into the expected format.
    """


class CalibrationNotFoundError(Exception):
    """Error raised when a calibration is not found.

    This error is specific to calibration operations and provides
    the ID of the calibration that was not found.

    Attributes:
        id: The ID of the calibration that was not found.
    """

    def __init__(self, calibration_id: UUID | str) -> None:
        """Initialize the calibration not found error.

        Args:
            calibration_id: The ID of the calibration that was not found.
        """
        message = f"Calibration not found: {calibration_id}"
        super().__init__(message)
        self.id = calibration_id

    def __str__(self) -> str:
        """Get the string representation of the error.

        Returns:
            str: The error message with the calibration ID.
        """
        return super().__str__()


class CalibrationConflictError(Exception):
    """Error raised when there is a conflict with a calibration.

    This error indicates that there is a conflict with the requested
    calibration operation, such as trying to create a duplicate calibration.

    Attributes:
        id: The ID of the calibration that caused the conflict.
    """

    def __init__(self, calibration_id: UUID | str) -> None:
        """Initialize the calibration conflict error.

        Args:
            calibration_id: The ID of the calibration that caused the conflict.
        """
        message = f"Calibration conflict found: {calibration_id}"
        super().__init__(message)
        self.id = calibration_id

    def __str__(self) -> str:
        """Get the string representation of the error.

        Returns:
            str: The error message with the calibration ID.
        """
        return super().__str__()
