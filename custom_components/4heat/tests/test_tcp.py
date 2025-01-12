"""Test TCP communication with 4Heat device."""

import asyncio
import json
import logging
import pytest

from tcp import TCPCommunication, TCPMessageTranslation

_LOGGER = logging.getLogger(__name__)


async def read_data(client: TCPCommunication):
    """Send a read command to the device."""
    _LOGGER.info("Initiate Read")
    response = await client.read_data()
    _LOGGER.info(response)
    if response:
        _LOGGER.info("Received Data:")
        json_data = json.loads(response)
        for data in json_data:
            _LOGGER.info(data)
    _LOGGER.info("End Read")


async def power_off(client: TCPCommunication):
    """Send a power off command to the device."""
    _LOGGER.info("Initiate Power Off")
    response = await client.power_off()
    _LOGGER.info(response)
    _LOGGER.info("End Power Off")


async def power_on(client: TCPCommunication):
    """Send a power on command to the device."""
    _LOGGER.info("Initiate Power On")
    response = await client.power_off()
    _LOGGER.info(response)
    _LOGGER.info("End Power On")


async def set_temperature(client: TCPCommunication, temperature: int = 21):
    """Send a set temperature command to the device."""
    _LOGGER.info("Initiate Set Temperature")
    response = await client.set_temperature(temperature)
    _LOGGER.info(response)
    _LOGGER.info("End Set Temperature")


def get_command(temperature: int, comando: str) -> str:
    """Get set Temperature command."""

    command_type = int(comando[:2], 16)
    if command_type == 1:  # th_all
        if temperature >= 16:
            temperature = f"{temperature:02X}"
        else:
            temperature = f"0{temperature:02X}"
        comando = f"05{comando[:10]}{temperature}{comando[12:]}"
    elif command_type == 14:  # par_value
        if temperature < 0:
            temperature += 65535
        if temperature >= 256:
            temperature = f"0{temperature:02X}"
        elif temperature >= 16:
            temperature = f"00{temperature:02X}"
        else:
            temperature = f"000{temperature:02X}"
        comando = f"05{comando[:6]}{temperature}"
    elif command_type == 18:  # testout
        if temperature < 0:
            temperature += 65535
        if temperature >= 256:
            temperature = f"0{temperature:02X}"
        elif temperature >= 16:
            temperature = f"00{temperature:02X}"
        else:
            temperature = f"000{temperature:02X}"
        comando = f"05{comando[:6]}{temperature}{comando[10:18]}"
    elif command_type == 34:  # th_all_2
        if temperature < 0:
            temperature += 65535
        if temperature >= 256:
            temperature = f"0{temperature:02X}"
        elif temperature >= 16:
            temperature = f"00{temperature:02X}"
        else:
            temperature = f"000{temperature:02X}"
        comando = f"05{comando[:10]}{temperature}{comando[14:]}"

    _LOGGER(f"comando aggiornato {comando}")
    return comando


# Run the test
def test_tcp_read():
    """Test tcp read."""
    logging.basicConfig(level=logging.INFO)
    tcp_client = TCPCommunication("192.168.1.18", 80)
    resp = asyncio.run(read_data(tcp_client))
    translation = TCPMessageTranslation()
    dev = translation.get_device_state(resp)
    assert dev is not None


#    asyncio.run(set_temperature(tcp_client, 21))
