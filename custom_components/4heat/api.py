"""4Heat API class."""

import logging
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    COMMAND_TURN_OFF,
    COMMAND_TURN_ON,
    # COMMAND_SET_TEMPERATURE,
)
from .device import Device

_LOGGER = logging.getLogger(__name__)


class API:
    """Class for 4Heat API."""

    def __init__(self, code: str, pin: str, user: str, pwd: str) -> None:
        """Initialise."""
        self.code = code
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
                    "Received response '%s' from API. Command %s", resp, command
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

        _LOGGER.debug("Trying Option 1")
        for s_command in device.set_temperature_command:
            command = self.get_command(s_command, temperature)

            if command != s_command:
                _LOGGER.debug("Trying command '%s'", command)

                # command = f'{COMMAND_SET_TEMPERATURE}e023100{temp_hex}"]'
                resp = await self.__send_command(token, command)
                _LOGGER.debug("Device returned '%s'", resp)

        _LOGGER.debug("Trying Option 2")
        for s_command in device.set_temperature_command:
            command = self.get_command2(s_command, temperature)

            if command != s_command:
                _LOGGER.debug("Trying command '%s'", command)

                # command = f'{COMMAND_SET_TEMPERATURE}e023100{temp_hex}"]'
                resp = await self.__send_command(token, command)
                _LOGGER.debug("Device returned '%s'", resp)

        return resp

    def get_command(self, comando, valore):
        """Get command."""
        comando_prefix = int(comando[:2], 16)

        if comando_prefix == 1:  # th_all
            if valore >= 16:
                valore = hex(valore)[2:]
            else:
                valore = "0" + hex(valore)[2:]
            comando = "05" + comando[:10] + valore + comando[12:]

        elif comando_prefix == 14:  # par_value
            if valore < 0:
                valore += 65535
                valore = hex(valore)[2:]
            elif valore >= 256:
                valore = "0" + hex(valore)[2:]
            elif valore >= 16:
                valore = "00" + hex(valore)[2:]
            else:
                valore = "000" + hex(valore)[2:]
            comando = "05" + comando[:6] + valore

        elif comando_prefix == 18:  # testout
            if valore < 0:
                valore += 65535
                valore = hex(valore)[2:]
            elif valore >= 256:
                valore = "0" + hex(valore)[2:]
            elif valore >= 16:
                valore = "00" + hex(valore)[2:]
            else:
                valore = "000" + hex(valore)[2:]
            comando = "05" + comando[:6] + valore + comando[10:28]

        elif comando_prefix == 34:  # th_all_2
            if valore < 0:
                valore += 65535
                valore = hex(valore)[2:]
            elif valore >= 256:
                valore = "0" + hex(valore)[2:]
            elif valore >= 16:
                valore = "00" + hex(valore)[2:]
            else:
                valore = "000" + hex(valore)[2:]
            comando = "05" + comando[:10] + valore + comando[14:]

        _LOGGER.debug("comando aggiornato %s", comando)

        return comando

    def get_command2(self, comando, valore):
        """Get command2."""

        if valore >= 16:
            valore = hex(valore)[2:]
        elif valore >= 0:
            valore = "0" + hex(valore)[2:]
        else:
            valore = 65536 + valore  # valore è negativo
            valore = hex(valore)[2:]
        # print(valore)

        if comando[:2] == "06":
            comando = "05" + comando[:4] + valore + comando[6:10]
        elif comando[:2] == "01":
            comando = "05" + comando[:10] + valore + comando[12:]
        elif comando[:2] == "0e":
            if len(valore) == 2:
                valore = "00" + valore
            elif len(valore) == 3:
                valore = "0" + valore
            comando = "05" + comando[:6] + valore
        elif comando[:2] == "12":
            if len(valore) == 2:
                valore = "00" + valore
            elif len(valore) == 3:
                valore = "0" + valore
            comando = "05" + comando[:6] + valore + comando[10:28]
        elif comando[:2] == "22":
            if len(valore) == 2:
                valore = "00" + valore
            elif len(valore) == 3:
                valore = "0" + valore
            comando = "05" + comando[:10] + valore + comando[14:]
        # print(comando)
        return comando


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
