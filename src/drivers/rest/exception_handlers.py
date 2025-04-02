from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from src.application.use_cases.exceptions import (
    CalibrationNotFoundError,
)
from src.entities.exceptions import (
    DatabaseOperationError,
    ExternalError,
    InputParseError,
    NotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """

    # Global HTTP exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(  # pyright: ignore [reportUnusedFunction]
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle any unhandled exceptions.

        Args:
            request: The incoming request.
            exc: The unhandled exception.

        Returns:
            JSONResponse: A 500 Internal Server Error response.
        """
        logger.error(f"Unexpected error: {exc!s}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(  # pyright: ignore [reportUnusedFunction]
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions.

        Args:
            request: The incoming request.
            exc: The HTTP exception.

        Returns:
            JSONResponse: A response with the appropriate status code and error details.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(DatabaseOperationError)
    async def db_operation_exception_handler(  # pyright: ignore [reportUnusedFunction]
        request: Request, exc: DatabaseOperationError
    ) -> JSONResponse:
        """Handle database operation errors.

        Args:
            request: The incoming request.
            exc: The database operation error.

        Returns:
            JSONResponse: A 500 Internal Server Error response.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InputParseError)
    async def input_parse_exception_handler(  # pyright: ignore [reportUnusedFunction]
        request: Request, exc: InputParseError
    ) -> JSONResponse:
        """Handle input parsing errors.

        Args:
            request: The incoming request.
            exc: The input parse error.

        Returns:
            JSONResponse: A 400 Bad Request response.
        """
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(  # pyright: ignore [reportUnusedFunction]
        request: Request, exc: NotFoundError
    ) -> JSONResponse:
        """Handle not found errors.

        Args:
            request: The incoming request.
            exc: The not found error.

        Returns:
            JSONResponse: A 404 Not Found response.
        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(CalibrationNotFoundError)
    async def calibration_not_found_exception_handler(  # pyright: ignore [reportUnusedFunction]
        request: Request,
        exc: CalibrationNotFoundError,
    ) -> JSONResponse:
        """Handle calibration not found errors.

        Args:
            request: The incoming request.
            exc: The calibration not found error.

        Returns:
            JSONResponse: A 404 Not Found response with calibration ID.
        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Calibration not found"},
        )

    @app.exception_handler(ExternalError)
    async def external_exception_handler(  # pyright: ignore [reportUnusedFunction]
        request: Request, exc: ExternalError
    ) -> JSONResponse:
        """Handle external service errors.

        Args:
            request: The incoming request.
            exc: The external service error.

        Returns:
            JSONResponse: A 500 Internal Server Error response.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )
