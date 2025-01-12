"""TCP communication module for 4Heat integration."""

import asyncio
import logging
import socket
from typing import Any

from .device import DeviceStatus

_LOGGER = logging.getLogger(__name__)


class TCPCommunication:
    """Class for TCP communication with 4Heat device."""

    def __init__(self, ip: str, port: int) -> None:
        """Initialise."""
        self.ip = ip
        self.port = port

    async def __receive_data(self, sock):
        """Receive data from the socket."""
        try:
            loop = asyncio.get_event_loop()
            received_data = await loop.run_in_executor(None, sock.recv, 1024)
            if received_data:
                data_str = received_data.decode()

            _LOGGER.debug("Received %s from %s", data_str, self.ip)

            return data_str
        finally:
            sock.close()

    async def __send_command(self, command: str) -> str:
        """Send a command to the specified IP address and port."""

        try:
            _LOGGER.debug("Sending %s to %s", command, self.ip)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, sock.connect, (self.ip, self.port))

            data_to_send = command.encode()
            await asyncio.sleep(0.5)  # Simulate delay
            await loop.run_in_executor(None, sock.sendall, data_to_send)

            response = await self.__receive_data(sock)
        except Exception as e:
            _LOGGER.error(e)
            raise TCPCommunicationError from e
        finally:
            sock.close()

        return response

    async def read_data(self) -> str:
        """Send power off command to the device."""
        command = '["2WL","1",""]'
        return await self.__send_command(command)

    async def power_on(self) -> str:
        """Send power on command to the device."""
        command = '["2WC","1","05040000"]'
        return await self.__send_command(command)

    async def power_off(self) -> str:
        """Send power off command to the device."""
        command = '["2WC","1","05050000"]'
        return await self.__send_command(command)

    async def set_temperature(self, temperature: int) -> str:
        """Send set temperature command to the device."""
        temp_hex = int(hex(temperature)[2:], 16)
        _LOGGER.info("Trying to set temperature to %s(0x%x)", temperature, temp_hex)
        command = '["2WC","1","050015011001000100000013"]'
        return await self.__send_command(command)


class TCPMessageTranslation:
    """Translate the received message from 4Heat devices."""

    def __convertSignedValue(self, value: int) -> int:
        """Convert a signed value to an integer."""
        if value > 32767:
            value = (65536 - value) * -1
        return value

    def read_command_response(self, command: str) -> dict:
        """Read a single command response and return the parsed response."""
        command_type = int(command[:2], 16)
        resp = {}

        if command_type == 1:  # th_all
            resp = {
                "command_type": "th_all",
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
                "id": int(command[2:4], 16),
                "parent": int(command[4:6], 16),
                "temperature": self.__convertSignedValue(int(command[6:10], 16)),
            }
        elif command_type == 3:  # th_state
            resp = {
                "command_type": "th_state",
                "id": int(command[2:4], 16),
                "parent": int(command[4:6], 16),
                "status": int(command[6:8], 16),
                "error_type": int(command[8:10], 16),
                "cod_error": int(command[10:12], 16),
            }
        elif command_type == 6:  # pw_all
            resp = {
                "command_type": "pw_all",
                "id": int(command[2:4], 16),
                "value": int(command[4:6], 16),
                "min": int(command[6:8], 16),
                "max": int(command[8:10], 16),
                "read_only": int(command[10:12], 16),
            }
        elif command_type == 8:  # crono_enb
            resp = {
                "command_type": "crono_enb",
                "id": int(command[2:4], 16),
                "status": int(command[4:6], 16),
                "mode": int(command[6:8], 16),
            }
        elif command_type == 11:  # stat_syst
            resp = {
                "command_type": "stat_syst",
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
                    "id": int(command[2:4], 16),
                    "stringa": str_value,
                }
            elif command[2:4] == "81":
                if len(command) == 28:
                    resp = {
                        "command_type": "state_info_81",
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
                    "temp_sec": self.__convertSignedValue(int(command[6:10], 16)),
                    "status": int(command[10:12], 16),
                    "cod_error": int(command[12:14], 16),
                    "temp_princ": self.__convertSignedValue(int(command[20:24], 16)),
                }
            else:
                resp = {
                    "command_type": "main_values",
                    "temp_sec": self.__convertSignedValue(int(command[6:10], 16)),
                    "status": int(command[10:12], 16),
                    "cod_error": int(command[12:14], 16),
                    "temp_princ": self.__convertSignedValue(int(command[20:24], 16)),
                    "pos_punto": int(command[36:38], 16),
                }
        elif command_type == 18:  # testout
            resp = {
                "command_type": "testout",
                "id": int(command[2:6], 16),
                "value": self.__convertSignedValue(int(command[6:10], 16)),
                "min": self.__convertSignedValue(int(command[10:14], 16)),
                "max": self.__convertSignedValue(int(command[14:18], 16)),
                "read_only": int(command[18:20], 16),
                "pos_punto": int(command[20:22], 16),
                "step_incr": int(command[22:26], 16),
                "test_timer": int(command[30:34], 16),
            }
        elif command_type == 34:  # th_all_2
            resp = {
                "command_type": "th_all_2",
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

    def get_device_state(self, received_data: dict[str, Any]) -> DeviceStatus:
        """Translate the received data and return the device status."""

        for data in received_data:
            _LOGGER.info(self.read_command_response(data))

        state = 0
        target_temperature = 0
        room_temperature = 0
        error_code = 0

        return DeviceStatus(state, target_temperature, room_temperature, error_code)


tcp_message_translation = TCPMessageTranslation()


class TCPCommunicationError(Exception):
    """Exception class for TCP communication error."""
