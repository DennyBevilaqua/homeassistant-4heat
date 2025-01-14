"""TCP communication module for 4Heat integration."""

import asyncio
import logging
import socket

from const import COMMAND_POWER_OFF, COMMAND_POWER_ON, COMMAND_SET_TEMPERATURE
from device import Device

_LOGGER = logging.getLogger(__name__)


class TCPCommunication:
    """Class for TCP communication with 4Heat device."""

    def __init__(self, ip: str, port: int) -> None:
        """Initialise."""
        self.ip = ip
        self.port = port

    async def __receive_data(self, sock) -> str:
        """Receive data from the socket."""
        data_str: str
        try:
            loop = asyncio.get_event_loop()
            received_data = await loop.run_in_executor(None, sock.recv, 1024)

            if received_data:
                data_str = received_data.decode()

            _LOGGER.debug("Received %s from %s", data_str, self.ip)
        finally:
            sock.close()

        return data_str

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
            _LOGGER.error("Error sending Command: %s", command)
            _LOGGER.error(e)
            raise TCPCommunicationError from e
        finally:
            sock.close()

        return response

    async def read_data(self) -> str:
        """Send power off command to the device."""
        command = COMMAND_POWER_ON
        return await self.__send_command(command)

    async def power_on(self) -> str:
        """Send power on command to the device."""
        command = '["2WC","1","05040000"]'
        return await self.__send_command(command)

    async def power_off(self) -> str:
        """Send power off command to the device."""
        command = COMMAND_POWER_OFF
        return await self.__send_command(command)

    async def set_temperature(self, device: Device, temperature: int) -> str:
        """Send set temperature command to the device."""
        temp_hex = hex(temperature)[2:]
        _LOGGER.debug("Trying to set temperature to %s(0x%s)", temperature, temp_hex)
        command = (
            f'{COMMAND_SET_TEMPERATURE}{temp_hex}{device.set_temperature_command}"]'
        )
        resp = await self.__send_command(command)
        _LOGGER.debug("Device returned %s", resp)
        return resp


class TCPCommunicationError(Exception):
    """Exception class for TCP communication error."""
