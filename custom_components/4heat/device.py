"""Device classes for 4Heat Integration."""

from datetime import datetime
import json
import logging
from typing import Any

from .const import DEVICE_ERRORS, TCP_PORT

_LOGGER = logging.getLogger(__name__)


class Device:
    """Represents the status of a 4Heat device."""

    state: int
    target_temperature: int
    room_temperature: int
    error_code: int
    state_timestamp: datetime
    last_update: datetime
    ip: str
    port = TCP_PORT
    name: str
    is_connected: bool
    software_version: str
    set_temperature_command: str

    def __init__(self) -> None:
        """Initialise."""
        self.state = 991
        self.target_temperature = 991
        self.room_temperature = 991
        self.error_code = 991
        self.state_timestamp = None
        self.last_update = None
        self.ip = None
        self.name = None
        self.is_connected = False
        self.software_version = None
        self.set_temperature_command = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize."""
        return self.__dict__

    @property
    def is_on(self) -> bool:
        """Property is on."""
        return self.state != 0

    @property
    def is_error(self) -> bool:
        """Property is error."""
        return self.error_code != 0

    @property
    def error_description(self) -> str:
        """Property error description."""

        if self.is_error:
            return DEVICE_ERRORS.get(str(self.error_code), "Unknown error")

        return ""

    @property
    def state_description(self) -> str:
        """Property state description."""

        if device_loader.state_descriptor:
            state_desc = next(
                (
                    item
                    for item in device_loader.state_descriptor
                    if item["val"] == self.state
                ),
                None,
            )

            if state_desc:
                return state_desc.get("descrizione_pt", "Unknown")

        return "Unknown"


class _DeviceLoader:
    """Translate the received message from 4Heat devices."""

    file_map = None
    main_thermostat: int = 12
    state_descriptor = []

    def initiate(self, file_map: dict[str, Any]) -> None:
        """Initialise DeviceLoader."""
        self.file_map = file_map

        if file_map:
            com_therm: dict[str, Any] = file_map.get("comandi_term_princ")
            if com_therm:
                self.main_thermostat = int(com_therm.get("scritt_termostato", 12)) - 1
            self.state_descriptor = file_map.get("lingue_stati", [])

    def __convertSignedValue(self, value: int) -> int:
        """Convert a signed value to an integer."""
        if value > 32767:
            value = (65536 - value) * -1
        return value

    def __read_command_response(self, command: str) -> dict:
        """Read a single command response and return the parsed response."""
        command_type = int(command[:2], 16)
        resp = {}

        if command_type == 1:  # th_all
            resp = {
                "command_type": "th_all",
                "command_code": command[:2],
                "id": int(command[2:4], 16),
                "parent": int(command[4:6], 16),
                "enablement": int(command[6:8], 16),
                "status": int(command[8:10], 16),
                "value": int(command[10:12], 16),
                "min": int(command[12:14], 16),
                "max": int(command[14:16], 16),
                "read_only": int(command[16:18], 16),
                "temperature": int(command[18:20], 16),
            }
        elif command_type == 2:  # th_temp
            resp = {
                "command_type": "th_temp",
                "command_code": command[:2],
                "id": int(command[2:4], 16),
                "parent": int(command[4:6], 16),
                "temperature": self.__convertSignedValue(int(command[6:10], 16)),
            }
        elif command_type == 3:  # th_state
            resp = {
                "command_type": "th_state",
                "command_code": command[:2],
                "id": int(command[2:4], 16),
                "parent": int(command[4:6], 16),
                "status": int(command[6:8], 16),
                "error_type": int(command[8:10], 16),
                "cod_error": int(command[10:12], 16),
            }
        elif command_type == 6:  # pw_all
            resp = {
                "command_type": "pw_all",
                "command_code": command[:2],
                "id": int(command[2:4], 16),
                "value": int(command[4:6], 16),
                "min": int(command[6:8], 16),
                "max": int(command[8:10], 16),
                "read_only": int(command[10:12], 16),
            }
        elif command_type == 8:  # crono_enb
            resp = {
                "command_type": "crono_enb",
                "command_code": command[:2],
                "id": int(command[2:4], 16),
                "status": int(command[4:6], 16),
                "mode": int(command[6:8], 16),
            }
        elif command_type == 11:  # stat_syst
            resp = {
                "command_type": "stat_syst",
                "command_code": command[:2],
                "id": int(command[2:4], 16),
                "status": int(command[4:6], 16),
                "var_status": int(command[6:8], 16),
            }
        elif command_type == 12:  # state_info
            if command[2:4] in ["00", "01", "80"]:
                str_value = "".join(
                    [
                        chr(int(command[i : i + 2], 16))
                        for i in range(4, len(command), 2)
                    ]
                )
                resp = {
                    "command_type": "state_info",
                    "command_code": command[:2],
                    "id": int(command[2:4], 16),
                    "stringa": str_value,
                }
            elif command[2:4] == "81":
                if len(command) == 28:
                    resp = {
                        "command_type": "state_info_81",
                        "command_code": command[:2],
                        "id": int(command[2:4], 16),
                        "status_crono": int(command[4:6], 16),
                        "liv_pot": chr(int(command[6:8], 16)),
                        "lang": int(command[8:10], 16),
                        "num_recipe": int(command[10:12], 16),
                        "ind_RS485": int(command[12:14], 16),
                        "thermostat": int(command[24:28], 16),
                    }
                else:
                    resp = {
                        "command_type": "state_info_81",
                        "command_code": command[:2],
                        "id": int(command[2:4], 16),
                        "status_crono": int(command[4:6], 16),
                        "liv_pot": chr(int(command[6:8], 16)),
                        "lang": int(command[8:10], 16),
                        "num_recipe": int(command[10:12], 16),
                        "ind_RS485": int(command[12:14], 16),
                        "thermostat": int(command[24:28], 16),
                        "pos_punto": int(command[28:30], 16),
                    }
        elif command_type == 14:  # par_value
            resp = {
                "command_type": "par_value",
                "command_code": command[:2],
                "id": int(command[2:6], 16),
                "value": self.__convertSignedValue(int(command[6:10], 16)),
                "min": self.__convertSignedValue(int(command[10:14], 16)),
                "max": self.__convertSignedValue(int(command[14:18], 16)),
                "read_only": int(command[18:20], 16),
                "pos_punto": int(command[20:22], 16),
                "step_incr": int(command[22:26], 16),
                "id_par": int(command[26:30], 16),
            }
        elif command_type == 16:  # main_values
            if len(command) == 36:
                resp = {
                    "command_type": "main_values",
                    "command_code": command[:2],
                    "temp_sec": self.__convertSignedValue(int(command[6:10], 16)),
                    "status": int(command[10:12], 16),
                    "cod_error": int(command[12:14], 16),
                    "temp_princ": self.__convertSignedValue(int(command[20:24], 16)),
                }
            else:
                resp = {
                    "command_type": "main_values",
                    "command_code": command[:2],
                    "temp_sec": self.__convertSignedValue(int(command[6:10], 16)),
                    "status": int(command[10:12], 16),
                    "cod_error": int(command[12:14], 16),
                    "temp_princ": self.__convertSignedValue(int(command[20:24], 16)),
                    "pos_punto": int(command[36:38], 16),
                }
        elif command_type == 18:  # testout
            resp = {
                "command_type": "testout",
                "command_code": command[:2],
                "id": int(command[2:6], 16),
                "value": self.__convertSignedValue(int(command[6:10], 16)),
                "min": self.__convertSignedValue(int(command[10:14], 16)),
                "max": self.__convertSignedValue(int(command[14:18], 16)),
                "read_only": int(command[18:20], 16),
                "pos_punto": int(command[20:22], 16),
                "step_incr": int(command[22:26], 16),
                "test_timer": int(command[30:34], 16),
                "set_temperature_command": command[10:28],
            }
        elif command_type == 34:  # th_all_2
            resp = {
                "command_type": "th_all_2",
                "command_code": command[:2],
                "id": int(command[2:4], 16),
                "parent": int(command[4:6], 16),
                "enablement": int(command[6:8], 16),
                "status": int(command[8:10], 16),
                "value": self.__convertSignedValue(int(command[10:14], 16)),
                "min": self.__convertSignedValue(int(command[14:18], 16)),
                "max": self.__convertSignedValue(int(command[18:22], 16)),
                "temperature": self.__convertSignedValue(int(command[26:30], 16)),
                "pos_punto": int(command[30:32], 16),
            }

        return resp

    def load_from_local(self, device: Device, received_data: str):
        """Translate the received data and return the device status."""

        _LOGGER.debug("Loading Device with local response data: %s", received_data)

        try:
            if received_data:
                json_data = json.loads(received_data)

                if json_data[0] == "2WL":
                    json_data.pop(0)
                    json_data.pop(0)

                for data in json_data:
                    resp = self.__read_command_response(data)
                    command_type = resp.get("command_type", "")

                    if command_type == "main_values":
                        main_resp = resp
                    elif data == json_data[self.main_thermostat]:
                        thermostate_resp = resp

                device.state = main_resp.get("status", 999)
                device.error_code = main_resp.get("cod_error", 999)
                device.room_temperature = main_resp.get("temp_princ", 0)

                device.target_temperature = thermostate_resp.get("value", 0)
                device.set_temperature_command = thermostate_resp.get(
                    "set_temperature_command", ""
                )

            device.last_update = datetime.now()
            device.state_timestamp = device.last_update
        except (KeyError, ValueError, TypeError) as e:
            raise DeviceDataLoadError from e

    def load_from_cloud(self, device: Device, received_data: dict[str, Any]):
        """Translate the received data and return the device status."""

        try:
            _LOGGER.debug("Loading Device with cloud response data: %s", received_data)

            device.name = received_data.get("Name")
            device.ip = received_data.get("IpAddress")
            device.is_connected = received_data.get("IsConnected")
            device.state_timestamp = datetime.fromisoformat(
                received_data.get("LastTimestamp")
            )
            device.software_version = f"{received_data.get("ProductVersion", 0).lstrip("0")}.{received_data.get("FirmwareVersion")}.{received_data.get("FirmwareRevision")}"

            last_message_received = received_data.get("LastMessageReceived")

            if last_message_received:
                json_last_msg = json.loads(last_message_received)
                values = json_last_msg.get("Values", None)

                if values:
                    for data in values:
                        resp = self.__read_command_response(data)
                        command_type = resp.get("command_type", "")

                        if command_type == "main_values":
                            main_resp = resp
                        elif data == values[self.main_thermostat]:
                            thermostate_resp = resp

                    device.state = main_resp.get("status", 999)
                    device.error_code = main_resp.get("cod_error", 999)
                    device.room_temperature = main_resp.get("temp_princ", 0)

                    device.target_temperature = thermostate_resp.get("value", 0)
                    device.set_temperature_command = thermostate_resp.get(
                        "set_temperature_command", ""
                    )

                    device.last_update = datetime.now()
        except (KeyError, ValueError, TypeError) as e:
            raise DeviceDataLoadError from e


device_loader = _DeviceLoader()


class DeviceDataLoadError(Exception):
    """Exception class for error when loading data to Device."""
