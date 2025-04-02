from dataclasses import dataclass
from enum import StrEnum


class CalibrationType(StrEnum):
    """
    Represents types of calibration.

    This enumeration is used to define different types of calibration utilized
    in systems where adjustments or corrections to values like gain, offset,
    pressure, or temperature are required.
    """

    gain = "gain"
    offset = "offset"
    pressure = "pressure"
    temp = "temperature"


@dataclass(frozen=True)
class Measurement:
    """
    A ValueObject representing a measurement with a specific value and calibration type.

    :ivar value: The numeric value of the measurement.
    :type value: float
    :ivar type: The calibration type associated with the measurement.
    :type type: CalibrationType
    """

    value: float
    type: CalibrationType
