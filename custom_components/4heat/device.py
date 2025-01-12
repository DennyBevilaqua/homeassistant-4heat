"""Device classes for 4Heat Integration."""

from .const import DEVICE_ERRORS


class DeviceStatus:
    """Represents the status of a 4Heat device."""

    def __init__(
        self,
        state: int,
        target_temperature: int,
        room_temperature: int,
        error_code: int,
    ) -> None:
        """Initialise."""
        self.state = state
        self.target_temperature = target_temperature
        self.room_temperature = room_temperature
        self.error_code = error_code

    @property
    def is_on(self) -> bool:
        """Property is on."""
        return self.state != 0

    @property
    def is_error(self) -> bool:
        """Property is error."""
        return self.error_code == 0

    @property
    def error_description(self) -> str:
        """Property error description."""

        if self.is_error:
            return DEVICE_ERRORS.get(str(self.error_code), "Unknown error")

        return ""
