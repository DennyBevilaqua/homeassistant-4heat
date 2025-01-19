"""4Heat API class."""

import logging
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    COMMAND_SET_TEMPERATURE,
    COMMAND_TURN_OFF,
    COMMAND_TURN_ON,
)
from .device import Device

_LOGGER = logging.getLogger(__name__)


class API:
    """Class for 4Heat API."""

    def __init__(self, code: str, pin: str, user: str, pwd: str) -> None:
        """Initialise."""
        self.code = code
        self.pin = pin
        self.user = user
        self.pwd = pwd

    async def get_token(self) -> dict[str, Any]:
        """Get api token."""
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"{API_BASE_URL}/Token",
                    data={
                        "grant_type": "password",
                        "username": self.user,
                        "password": self.pwd,
                    },
                    timeout=120,
                )

                return await response.json()
        except Exception as err:
            _LOGGER.error(err)
            raise APIAuthError("Error getting token") from err

    async def get_file_map(self, token: dict[str, Any]) -> dict[str, Any]:
        """Get Device File Map."""
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.get(
                    f"{API_BASE_URL}/api/Devices/FileMap?pin={self.pin}&id={self.code}",
                    headers={"Authorization": f"Bearer {token.get("access_token")}"},
                    timeout=120,
                )

                return await response.json()
        except Exception as err:
            _LOGGER.error(err)
            raise APIConnectionError(
                "It was not possible to get the file map from API"
            ) from err

    async def get_data(self, token: dict[str, Any]) -> dict[str, Any]:
        """Get api data."""
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.get(
                    f"{API_BASE_URL}/api/devices/Details?id={self.code}",
                    headers={"Authorization": f"Bearer {token.get("access_token")}"},
                    timeout=120,
                )

                return await response.json()
        except Exception as err:
            _LOGGER.error(err)
            raise APIConnectionError(
                "It was not possible to get data from API"
            ) from err

    async def __send_command(self, token: dict[str, Any], command: str) -> str:
        """Send command to api."""
        try:
            _LOGGER.debug("Sending command %s to API", command)

            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"{API_BASE_URL}/api/devices/command?id={self.code}&comando={command}",
                    headers={"Authorization": f"Bearer {token.get("access_token")}"},
                    timeout=120,
                )

                resp = await response.text()

                _LOGGER.debug(
                    "Received response '%s' from API. Command '%s'", resp, command
                )

                return resp
        except Exception as err:
            _LOGGER.error(err)
            raise APIConnectionError(
                "It was not possible to send command to API"
            ) from err

        return True

    async def turn_on(self, token: dict[str, Any]) -> str:
        """Send power on command to the device."""
        command = COMMAND_TURN_ON
        return await self.__send_command(token, command)

    async def turn_off(self, token: dict[str, Any]) -> str:
        """Send power off command to the device."""
        command = COMMAND_TURN_OFF
        return await self.__send_command(token, command)

    async def set_temperature(
        self, device: Device, token: dict[str, Any], temperature: int
    ) -> str:
        """Send set temperature command to the device."""
        temp_hex = hex(temperature)[2:]
        _LOGGER.debug("Trying to set temperature to %s(0x%s)", temperature, temp_hex)

        if len(temp_hex) == 1:
            temp_hex = f"000{temp_hex}"
        elif len(temp_hex) == 2:
            temp_hex = f"00{temp_hex}"
        else:
            raise APIConnectionError("Target temperature is invalid")

        command = (
            f'{COMMAND_SET_TEMPERATURE}{temp_hex}{device.set_temperature_command}"]'
        )

        return await self.__send_command(token, command)


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
