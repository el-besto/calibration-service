from typing import TYPE_CHECKING

from src.application.use_cases.calibrations.add_calibration_use_case import (
    AddCalibrationOutput,
)
from src.application.use_cases.calibrations.list_calibrations import (
    ListCalibrationsOutput,
)
from src.drivers.rest.schemas.calibration_schemas import (
    CalibrationCreateResponse,
    CalibrationListResponse,
    CalibrationReadResponse,
)
from src.entities.models.calibration import Calibration

if TYPE_CHECKING:
    from src.application.dtos.get_tags_for_calibration_dtos import (
        GetTagsForCalibrationOutput,
    )


class CalibrationPresenter:
    """Presenter for converting calibration entities to response schemas.

    This class is responsible for transforming internal calibration entities
    into API response schemas.
    """

    @staticmethod
    def present_calibration(calibration: Calibration) -> CalibrationReadResponse:
        """Converts a Calibration entity to a CalibrationReadResponse schema."""
        return CalibrationReadResponse(
            calibration_id=calibration.id,
            value=calibration.measurement.value,
            calibration_type=calibration.measurement.type,
            timestamp=calibration.timestamp.to_datetime(),
            username=calibration.username,
            tags=[tag.name for tag in calibration.tags],
        )

    @staticmethod
    def present_calibration_list(
        calibrations: list[Calibration],
    ) -> list[CalibrationReadResponse]:
        """Converts a list of Calibration entities to a list of CalibrationReadResponse schemas."""
        return [CalibrationPresenter.present_calibration(cal) for cal in calibrations]

    @staticmethod
    def present_calibration_creation(
        output_dto: AddCalibrationOutput,
    ) -> CalibrationCreateResponse:
        """Formats the output of the AddCalibrationUseCase into the API response."""
        return CalibrationCreateResponse(
            calibration_id=output_dto.created_calibration.id
        )

    @staticmethod
    def present_list_output(
        output_dto: ListCalibrationsOutput,
    ) -> CalibrationListResponse:
        """Formats the output of the ListCalibrationsUseCase."""
        formatted_calibrations = CalibrationPresenter.present_calibration_list(
            output_dto.calibrations
        )
        return CalibrationListResponse(calibrations=formatted_calibrations)

    @staticmethod
    def present_calibration_tags(
        output_dto: "GetTagsForCalibrationOutput",
    ) -> list[str]:
        """Presents the list of tag names from the GetTagsForCalibrationOutput DTO."""
        # Currently just returns the list directly, but provides an extension point
        return output_dto.tag_names
